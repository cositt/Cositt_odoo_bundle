from odoo.tests.common import TransactionCase


class TestCosittDuplicateContacts(TransactionCase):
    def test_group_by_phone_field_exists(self):
        self.assertIn(
            "group_by_phone_sanitized",
            self.env["base.partner.merge.automatic.wizard"]._fields,
        )

    def test_detects_duplicates_by_phone_regardless_of_format(self):
        p1 = self.env["res.partner"].create(
            {"name": "Duplicado Uno", "phone": "+34 610 555 444"}
        )
        p2 = self.env["res.partner"].create(
            {"name": "Duplicado Dos", "phone": "+34610555444"}
        )
        self.assertTrue(p1.phone_sanitized)
        self.assertEqual(p1.phone_sanitized, p2.phone_sanitized)

        wizard = self.env["base.partner.merge.automatic.wizard"].create(
            {"group_by_phone_sanitized": True}
        )
        # Sin flush manual: la corrección debe encargarse de esto sola.
        wizard.action_start_manual_process()

        self.assertEqual(wizard.state, "selection")
        self.assertEqual(set(wizard.partner_ids.ids), {p1.id, p2.id})

    def test_partners_without_phone_are_not_grouped_together(self):
        # Regresión: sin el ajuste de _generate_query, todos los contactos
        # sin teléfono (NULL) se agruparían como "duplicados" entre sí,
        # porque SQL GROUP BY junta los NULL en un mismo grupo.
        self.env["res.partner"].create({"name": "Sin Telefono Uno"})
        self.env["res.partner"].create({"name": "Sin Telefono Dos"})
        self.env["res.partner"].create({"name": "Sin Telefono Tres"})

        wizard = self.env["base.partner.merge.automatic.wizard"].create(
            {"group_by_phone_sanitized": True}
        )
        wizard.action_start_manual_process()

        self.assertEqual(wizard.state, "finished")
        self.assertEqual(wizard.number_group, 0)

    def test_other_group_by_criteria_still_work(self):
        # No debe romper el comportamiento nativo (email/name/vat/etc.).
        p1 = self.env["res.partner"].create(
            {"name": "Mismo Email", "email": "mismo@ejemplo.com"}
        )
        p2 = self.env["res.partner"].create(
            {"name": "Otro Nombre", "email": "mismo@ejemplo.com"}
        )
        wizard = self.env["base.partner.merge.automatic.wizard"].create(
            {"group_by_email": True}
        )
        wizard.action_start_manual_process()

        self.assertEqual(wizard.state, "selection")
        self.assertEqual(set(wizard.partner_ids.ids), {p1.id, p2.id})

    def test_combining_phone_with_email_uses_and_semantics(self):
        # Comportamiento nativo de Odoo (no algo que este módulo cambie):
        # marcar dos criterios exige coincidir en AMBOS a la vez. Comparten
        # teléfono pero no email, así que con los dos marcados no deben
        # agruparse.
        self.env["res.partner"].create(
            {"name": "Solo Telefono Uno", "phone": "+34 699 111 222"}
        )
        self.env["res.partner"].create(
            {"name": "Solo Telefono Dos", "phone": "699111222"}
        )
        wizard = self.env["base.partner.merge.automatic.wizard"].create(
            {"group_by_email": True, "group_by_phone_sanitized": True}
        )
        wizard.action_start_manual_process()

        self.assertEqual(wizard.state, "finished")
        self.assertEqual(wizard.number_group, 0)

    def test_merge_by_phone_group_removes_duplicate(self):
        # action_start_automatic_process hace cr.commit() internamente
        # (comportamiento del propio core, no de este módulo), incompatible
        # con TransactionCase. Se prueba el mismo camino que usan los tests
        # del core: detectar con action_start_manual_process y fusionar el
        # grupo encontrado llamando _merge directamente.
        p1 = self.env["res.partner"].create(
            {"name": "Automerge Uno", "phone": "+34 688 222 333"}
        )
        p2 = self.env["res.partner"].create(
            {"name": "Automerge Dos", "phone": "688222333"}
        )
        wizard = self.env["base.partner.merge.automatic.wizard"].create(
            {"group_by_phone_sanitized": True}
        )
        wizard.action_start_manual_process()
        self.assertEqual(set(wizard.partner_ids.ids), {p1.id, p2.id})

        wizard._merge(wizard.partner_ids.ids, wizard.dst_partner_id)

        remaining = (p1 + p2).exists()
        self.assertEqual(len(remaining), 1)

    def test_action_and_menu_point_to_merge_wizard(self):
        action = self.env.ref(
            "cositt_duplicate_contacts.action_cositt_duplicate_contacts"
        )
        self.assertEqual(action.res_model, "base.partner.merge.automatic.wizard")

        menu = self.env.ref("cositt_duplicate_contacts.menu_cositt_duplicate_contacts")
        self.assertEqual(menu.action.res_model, "base.partner.merge.automatic.wizard")
