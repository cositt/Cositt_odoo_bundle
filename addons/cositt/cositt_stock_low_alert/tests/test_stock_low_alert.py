from unittest.mock import patch

from odoo.tests.common import BaseCase, TransactionCase

from ..models.product_template import _is_low_stock


class TestIsLowStock(BaseCase):
    def test_true_when_at_threshold(self):
        self.assertTrue(_is_low_stock(5, 5))

    def test_true_when_below_threshold(self):
        self.assertTrue(_is_low_stock(2, 5))

    def test_false_when_above_threshold(self):
        self.assertFalse(_is_low_stock(10, 5))

    def test_false_when_threshold_is_zero(self):
        self.assertFalse(_is_low_stock(0, 0))

    def test_false_when_threshold_is_negative(self):
        self.assertFalse(_is_low_stock(-5, -1))

    def test_false_when_threshold_is_false(self):
        self.assertFalse(_is_low_stock(0, False))


class TestProductTemplateLowStock(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.location = cls.env.ref("stock.stock_location_stock")
        cls.user = cls.env["res.users"].create(
            {"name": "Responsable Inventario", "login": "stock_alert_test@example.com"}
        )

    def _set_quantity(self, product, qty):
        self.env["stock.quant"]._update_available_quantity(
            product.product_variant_id, self.location, qty
        )

    def test_is_low_stock_true_below_threshold(self):
        product = self.env["product.template"].create(
            {"name": "Producto Bajo Stock", "is_storable": True, "low_stock_threshold": 10}
        )
        self._set_quantity(product, 3)
        self.assertTrue(product.is_low_stock)

    def test_is_low_stock_false_above_threshold(self):
        product = self.env["product.template"].create(
            {"name": "Producto Con Stock", "is_storable": True, "low_stock_threshold": 10}
        )
        self._set_quantity(product, 50)
        self.assertFalse(product.is_low_stock)

    def test_is_low_stock_false_when_threshold_disabled(self):
        # Producto recién creado, sin quants: qty_available ya es 0 por
        # defecto, no hace falta (ni se puede) forzar un quant a 0.
        product = self.env["product.template"].create(
            {"name": "Sin Umbral", "is_storable": True, "low_stock_threshold": 0}
        )
        self.assertFalse(product.is_low_stock)


class TestCronCheckLowStock(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.location = cls.env.ref("stock.stock_location_stock")
        cls.Product = cls.env["product.template"]
        cls.user = cls.env["res.users"].create(
            {"name": "Responsable Inventario", "login": "cron_stock_alert_test@example.com"}
        )
        cls.todo_activity_type = cls.env.ref("mail.mail_activity_data_todo")
        cls.alert_activity_type = cls.env.ref(
            "cositt_stock_low_alert.mail_activity_type_low_stock_alert"
        )

    def _low_stock_product(self, responsible=None, qty=1, threshold=10):
        product = self.Product.create(
            {
                "name": "Producto Test",
                "is_storable": True,
                "low_stock_threshold": threshold,
                "responsible_id": responsible.id if responsible else False,
            }
        )
        if qty:
            self.env["stock.quant"]._update_available_quantity(
                product.product_variant_id, self.location, qty
            )
        return product

    def test_creates_activity_when_low_and_responsible_set(self):
        product = self._low_stock_product(responsible=self.user)
        self.Product._cron_check_low_stock()
        activities = product.activity_ids.filtered(
            lambda a: a.activity_type_id == self.alert_activity_type
        )
        self.assertEqual(len(activities), 1)
        self.assertEqual(activities.user_id, self.user)

    def test_does_not_duplicate_activity_on_second_run(self):
        product = self._low_stock_product(responsible=self.user)
        self.Product._cron_check_low_stock()
        self.Product._cron_check_low_stock()
        activities = product.activity_ids.filtered(
            lambda a: a.activity_type_id == self.alert_activity_type
        )
        self.assertEqual(len(activities), 1)

    def test_unrelated_todo_activity_does_not_block_alert(self):
        # Regresión HIGH del review: reutilizar el "To-Do" genérico para
        # el chequeo de "ya avisado" silenciaba el aviso real si el
        # producto ya tenía un To-Do abierto por cualquier otro motivo.
        # Ahora se usa un tipo de actividad propio, así que un To-Do
        # ajeno no debe impedir la creación del aviso.
        product = self._low_stock_product(responsible=self.user)
        product.activity_schedule(
            "mail.mail_activity_data_todo", summary="Llamar al proveedor"
        )
        self.Product._cron_check_low_stock()
        alerts = product.activity_ids.filtered(
            lambda a: a.activity_type_id == self.alert_activity_type
        )
        self.assertEqual(len(alerts), 1)

    def test_skips_when_no_responsible(self):
        product = self._low_stock_product(responsible=None)
        self.Product._cron_check_low_stock()
        self.assertFalse(product.activity_ids)

    def test_skips_products_above_threshold(self):
        product = self._low_stock_product(responsible=self.user, qty=100, threshold=10)
        self.Product._cron_check_low_stock()
        self.assertFalse(product.activity_ids)

    def test_skips_products_with_threshold_disabled(self):
        product = self._low_stock_product(responsible=self.user, qty=0, threshold=0)
        self.Product._cron_check_low_stock()
        self.assertFalse(product.activity_ids)

    def test_creates_activity_when_product_has_own_company(self):
        # Regresión HIGH del review: responsible_id es company_dependent
        # y el cron corre con el contexto de una sola compañía. Para un
        # producto con company_id propio, el código fuerza ese contexto
        # explícitamente en vez de dejarlo al azar del usuario del cron.
        product = self._low_stock_product(responsible=self.user)
        product.company_id = self.env.company
        self.Product._cron_check_low_stock()
        alerts = product.activity_ids.filtered(
            lambda a: a.activity_type_id == self.alert_activity_type
        )
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts.user_id, self.user)

    def test_cron_isolates_failure_per_product(self):
        # Un fallo creando el aviso de un producto no debe impedir que se
        # cree el de otro producto en la misma pasada del cron.
        broken_product = self._low_stock_product(responsible=self.user)
        healthy_product = self._low_stock_product(responsible=self.user)

        original_schedule = broken_product.__class__.activity_schedule
        broken_id = broken_product.id

        def fake_schedule(self, *args, **kwargs):
            if self.id == broken_id:
                raise RuntimeError("boom")
            return original_schedule(self, *args, **kwargs)

        with patch.object(type(broken_product), "activity_schedule", fake_schedule):
            self.Product._cron_check_low_stock()

        self.assertFalse(broken_product.activity_ids)
        self.assertTrue(healthy_product.activity_ids)
