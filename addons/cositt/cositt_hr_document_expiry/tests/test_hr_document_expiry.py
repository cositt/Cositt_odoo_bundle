from datetime import date, timedelta

from odoo.exceptions import ValidationError
from odoo.tests.common import BaseCase, TransactionCase

from ..models.hr_employee_document import _document_expiry_state

TODAY = date(2026, 6, 15)


class TestDocumentExpiryState(BaseCase):
    """Función pura, sin ORM ni fields.Date.today() — se le pasa "today"
    explícito para que el test no dependa del reloj real."""

    def test_valid_when_far_in_future(self):
        expiry = TODAY + timedelta(days=60)
        self.assertEqual(_document_expiry_state(expiry, 30, TODAY), "valid")

    def test_expiring_soon_inside_window(self):
        expiry = TODAY + timedelta(days=10)
        self.assertEqual(_document_expiry_state(expiry, 30, TODAY), "expiring_soon")

    def test_expiring_soon_at_alert_boundary(self):
        # alert_date == today: primer día dentro de la ventana.
        expiry = TODAY + timedelta(days=30)
        self.assertEqual(_document_expiry_state(expiry, 30, TODAY), "expiring_soon")

    def test_expiring_soon_on_expiry_day_itself(self):
        # El propio día de caducidad todavía no se considera "caducado".
        expiry = TODAY
        self.assertEqual(_document_expiry_state(expiry, 30, TODAY), "expiring_soon")

    def test_expired_the_day_after(self):
        expiry = TODAY - timedelta(days=1)
        self.assertEqual(_document_expiry_state(expiry, 30, TODAY), "expired")

    def test_expired_long_ago(self):
        expiry = TODAY - timedelta(days=400)
        self.assertEqual(_document_expiry_state(expiry, 30, TODAY), "expired")

    def test_no_expiry_date_is_valid(self):
        self.assertEqual(_document_expiry_state(False, 30, TODAY), "valid")

    def test_zero_reminder_days_only_flags_on_expiry_day(self):
        self.assertEqual(_document_expiry_state(TODAY, 0, TODAY), "expiring_soon")
        self.assertEqual(
            _document_expiry_state(TODAY + timedelta(days=1), 0, TODAY), "valid"
        )


class TestHrEmployeeDocumentModel(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.employee = cls.env["hr.employee"].create({"name": "Empleado de Prueba"})

    def test_alert_date_is_computed_from_expiry_and_reminder(self):
        doc = self.env["hr.employee.document"].create(
            {
                "employee_id": self.employee.id,
                "name": "DNI",
                "expiry_date": date(2026, 12, 31),
                "reminder_days_before": 30,
            }
        )
        self.assertEqual(doc.alert_date, date(2026, 12, 1))

    def test_state_reflects_real_dates(self):
        doc = self.env["hr.employee.document"].create(
            {
                "employee_id": self.employee.id,
                "name": "Permiso caducado",
                "expiry_date": date.today() - timedelta(days=5),
                "reminder_days_before": 30,
            }
        )
        self.assertEqual(doc.state, "expired")

    def test_negative_reminder_days_raises(self):
        with self.assertRaises(ValidationError):
            self.env["hr.employee.document"].create(
                {
                    "employee_id": self.employee.id,
                    "name": "DNI",
                    "expiry_date": date(2026, 12, 31),
                    "reminder_days_before": -1,
                }
            )

    def test_expiry_date_is_required(self):
        with self.assertRaises(Exception):
            self.env["hr.employee.document"].create(
                {"employee_id": self.employee.id, "name": "DNI"}
            )

    def test_company_id_follows_employee(self):
        doc = self.env["hr.employee.document"].create(
            {
                "employee_id": self.employee.id,
                "name": "DNI",
                "expiry_date": date(2026, 12, 31),
            }
        )
        self.assertEqual(doc.company_id, self.employee.company_id)

    def test_multi_company_rule_hides_other_company_documents(self):
        # Regresión HIGH del review: sin ir.rule, un usuario con
        # hr.group_hr_user podía leer documentos (DNI, permiso de
        # trabajo...) de empleados de OTRA compañía.
        other_company = self.env["res.company"].create({"name": "Otra Compañía"})
        other_employee = self.env["hr.employee"].create(
            {"name": "Empleado Otra Compañía", "company_id": other_company.id}
        )
        other_doc = self.env["hr.employee.document"].create(
            {
                "employee_id": other_employee.id,
                "name": "DNI ajeno",
                "expiry_date": date(2026, 12, 31),
            }
        )

        hr_user = self.env["res.users"].create(
            {
                "name": "HR de la compañía principal",
                "login": "hr_multicompany_test@example.com",
                "group_ids": [(4, self.env.ref("hr.group_hr_user").id)],
                "company_ids": [(6, 0, [self.env.company.id])],
                "company_id": self.env.company.id,
            }
        )
        found = (
            self.env["hr.employee.document"]
            .with_user(hr_user)
            .search([("id", "=", other_doc.id)])
        )
        self.assertFalse(found)

    def test_archiving_keeps_record_but_hides_from_default_search(self):
        doc = self.env["hr.employee.document"].create(
            {
                "employee_id": self.employee.id,
                "name": "Carné caducado, ya renovado",
                "expiry_date": date(2020, 1, 1),
                "reminder_days_before": 30,
            }
        )
        doc.active = False
        found = self.env["hr.employee.document"].search([("id", "=", doc.id)])
        self.assertFalse(found)
        found_all = self.env["hr.employee.document"].with_context(
            active_test=False
        ).search([("id", "=", doc.id)])
        self.assertTrue(found_all)


class TestCronCheckExpiringDocuments(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Document = cls.env["hr.employee.document"]
        cls.user = cls.env["res.users"].create(
            {"name": "Empleado Usuario", "login": "empleado_doc_test@example.com"}
        )
        cls.employee_with_user = cls.env["hr.employee"].create(
            {"name": "Con Usuario", "user_id": cls.user.id}
        )
        cls.employee_without_user = cls.env["hr.employee"].create(
            {"name": "Sin Usuario"}
        )
        cls.todo_activity_type = cls.env.ref("mail.mail_activity_data_todo")

    def _expiring_soon_document(self, employee):
        return self.Document.create(
            {
                "employee_id": employee.id,
                "name": "DNI",
                "expiry_date": date.today() + timedelta(days=5),
                "reminder_days_before": 30,
            }
        )

    def test_creates_activity_for_document_in_alert_window(self):
        doc = self._expiring_soon_document(self.employee_with_user)
        self.Document._cron_check_expiring_documents()
        activities = doc.activity_ids.filtered(
            lambda a: a.activity_type_id == self.todo_activity_type
        )
        self.assertEqual(len(activities), 1)
        self.assertEqual(activities.user_id, self.user)

    def test_does_not_duplicate_activity_on_second_run(self):
        doc = self._expiring_soon_document(self.employee_with_user)
        self.Document._cron_check_expiring_documents()
        self.Document._cron_check_expiring_documents()
        activities = doc.activity_ids.filtered(
            lambda a: a.activity_type_id == self.todo_activity_type
        )
        self.assertEqual(len(activities), 1)

    def test_skips_documents_still_valid(self):
        doc = self.Document.create(
            {
                "employee_id": self.employee_with_user.id,
                "name": "Pasaporte",
                "expiry_date": date.today() + timedelta(days=200),
                "reminder_days_before": 30,
            }
        )
        self.Document._cron_check_expiring_documents()
        self.assertFalse(doc.activity_ids)

    def test_falls_back_to_manager_when_employee_has_no_user(self):
        self.employee_without_user.parent_id = self.employee_with_user
        doc = self._expiring_soon_document(self.employee_without_user)
        self.Document._cron_check_expiring_documents()
        activities = doc.activity_ids.filtered(
            lambda a: a.activity_type_id == self.todo_activity_type
        )
        self.assertEqual(activities.user_id, self.user)

    def test_skips_gracefully_when_no_responsible_available(self):
        doc = self._expiring_soon_document(self.employee_without_user)
        # No debe lanzar excepción aunque no haya nadie a quien asignar.
        self.Document._cron_check_expiring_documents()
        self.assertFalse(doc.activity_ids)

    def test_ignores_archived_documents(self):
        doc = self._expiring_soon_document(self.employee_with_user)
        doc.active = False
        self.Document._cron_check_expiring_documents()
        self.assertFalse(doc.activity_ids)

    def test_also_reminds_for_already_expired_documents(self):
        doc = self.Document.create(
            {
                "employee_id": self.employee_with_user.id,
                "name": "Permiso Caducado",
                "expiry_date": date.today() - timedelta(days=10),
                "reminder_days_before": 30,
            }
        )
        self.Document._cron_check_expiring_documents()
        self.assertTrue(doc.activity_ids)
