import ast

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestEmailDomainCompute(TransactionCase):
    def test_email_domain_computed_from_email(self):
        partner = self.env["res.partner"].create(
            {"name": "Pedro", "email": "pedro@acme.com"}
        )
        self.assertEqual(partner.email_domain, "acme.com")

    def test_email_domain_false_without_email(self):
        partner = self.env["res.partner"].create({"name": "Sin Email"})
        self.assertFalse(partner.email_domain)

    def test_email_domain_recomputes_on_email_change(self):
        partner = self.env["res.partner"].create(
            {"name": "Pedro", "email": "pedro@acme.com"}
        )
        partner.email = "pedro@otra-empresa.com"
        self.assertEqual(partner.email_domain, "otra-empresa.com")

    def test_email_domain_lowercased(self):
        partner = self.env["res.partner"].create(
            {"name": "Pedro", "email": "Pedro@ACME.com"}
        )
        self.assertEqual(partner.email_domain, "acme.com")


class TestFindCompanyByDomain(TransactionCase):
    def setUp(self):
        super().setUp()
        self.company = self.env["res.partner"].create(
            {"name": "Acme SA", "is_company": True, "email": "info@acme.com"}
        )

    def test_links_unique_match(self):
        contact = self.env["res.partner"].create(
            {"name": "Pedro", "email": "pedro@acme.com"}
        )
        result = contact.action_find_company_by_domain()

        self.assertEqual(contact.parent_id, self.company)
        self.assertEqual(result["type"], "ir.actions.client")
        self.assertEqual(result["params"]["type"], "success")

    def test_requires_email(self):
        contact = self.env["res.partner"].create({"name": "Sin Email"})
        with self.assertRaises(UserError):
            contact.action_find_company_by_domain()

    def test_rejects_free_email_provider(self):
        contact = self.env["res.partner"].create(
            {"name": "Pedro", "email": "pedro@gmail.com"}
        )
        with self.assertRaises(UserError):
            contact.action_find_company_by_domain()

    def test_no_match_raises(self):
        contact = self.env["res.partner"].create(
            {"name": "Pedro", "email": "pedro@sin-empresa-registrada.com"}
        )
        with self.assertRaises(UserError):
            contact.action_find_company_by_domain()

    def test_ambiguous_multiple_companies_raises(self):
        self.env["res.partner"].create(
            {"name": "Acme Sucursal", "is_company": True, "email": "otra@acme.com"}
        )
        contact = self.env["res.partner"].create(
            {"name": "Pedro", "email": "pedro@acme.com"}
        )
        with self.assertRaises(UserError):
            contact.action_find_company_by_domain()

    def test_already_linked_raises(self):
        contact = self.env["res.partner"].create(
            {
                "name": "Pedro",
                "email": "pedro@acme.com",
                "parent_id": self.company.id,
            }
        )
        with self.assertRaises(UserError):
            contact.action_find_company_by_domain()

    def test_rejects_when_self_is_company(self):
        with self.assertRaises(UserError):
            self.company.action_find_company_by_domain()

    def test_linked_to_different_company_raises_without_overwriting(self):
        # Regresión: si el contacto ya estaba vinculado a OTRA empresa (p.ej.
        # asignada a mano), el botón no debe reasignar el vínculo en
        # silencio y perder esa relación sin avisar.
        other_company = self.env["res.partner"].create(
            {"name": "Otra Empresa SA", "is_company": True}
        )
        contact = self.env["res.partner"].create(
            {
                "name": "Pedro",
                "email": "pedro@acme.com",
                "parent_id": other_company.id,
            }
        )
        with self.assertRaises(UserError):
            contact.action_find_company_by_domain()
        self.assertEqual(contact.parent_id, other_company)


class TestEmailDomainViews(TransactionCase):
    def test_form_view_extension_is_installed(self):
        view = self.env.ref(
            "cositt_email_domain_helper.view_partner_form_inherit_email_domain_helper"
        )
        self.assertEqual(view.inherit_id, self.env.ref("base.view_partner_form"))

    def test_button_placed_in_header_not_child_contacts_template(self):
        # Regresión: el botón debe quedar anclado a la cabecera principal
        # (nombre/email/teléfono), no a la plantilla de contactos hijos que
        # vive dentro del <notebook> más abajo en la misma vista base.
        view = self.env["res.partner"].get_view(
            view_id=self.env.ref("base.view_partner_form").id, view_type="form"
        )
        arch = view["arch"]

        self.assertEqual(arch.count("action_find_company_by_domain"), 1)
        button_pos = arch.index("action_find_company_by_domain")
        notebook_pos = arch.index("<notebook")
        self.assertLess(button_pos, notebook_pos)

    def test_duplicates_action_domain_and_context(self):
        action = self.env.ref(
            "cositt_email_domain_helper.action_cositt_email_domain_duplicates"
        )
        self.assertIn(
            ("is_company", "=", True),
            action.domain and ast.literal_eval(action.domain),
        )
        self.assertTrue(action.context and "group_by_email_domain" in action.context)
