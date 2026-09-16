from pathlib import Path

from odoo.fields import Command
from odoo.tests.common import TransactionCase


class TestCosittListColumnPreference(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Preference = cls.env["cositt.list.column.preference"]
        cls.admin = cls.env.ref("base.user_admin")
        # Se reutiliza base.public_user en vez de crear un res.users
        # nuevo: res.users.create() falla bajo --test-enable en este
        # entorno (ver memoria del proyecto), y quitarle group_system a
        # base.user_admin dispara la validación propia de Odoo "debe
        # haber al menos un administrador" (es el único admin de esta
        # base) — mismo criterio ya usado en cositt_attachment_lock.
        cls.other_user = cls.env.ref("base.public_user")
        cls.other_user.group_ids = [
            Command.unlink(cls.env.ref("base.group_public").id),
            Command.link(cls.env.ref("base.group_user").id),
        ]

    # --- get/set: comportamiento normal -----------------------------------

    def test_get_returns_false_when_nothing_saved(self):
        result = self.Preference.with_user(self.admin).cositt_get_active_fields(
            "res.partner,list,123,phone,email"
        )
        self.assertFalse(result)

    def test_set_then_get_roundtrip(self):
        key = "res.partner,list,123,phone,email"
        self.Preference.with_user(self.admin).cositt_set_active_fields(key, "phone,email")

        result = self.Preference.with_user(self.admin).cositt_get_active_fields(key)

        self.assertEqual(result, "phone,email")

    def test_set_twice_updates_instead_of_duplicating(self):
        key = "res.partner,list,123,phone,email"
        self.Preference.with_user(self.admin).cositt_set_active_fields(key, "phone")
        self.Preference.with_user(self.admin).cositt_set_active_fields(key, "phone,email")

        count = self.Preference.with_user(self.admin).search_count([
            ("user_id", "=", self.admin.id), ("view_key", "=", key),
        ])
        result = self.Preference.with_user(self.admin).cositt_get_active_fields(key)

        self.assertEqual(count, 1)
        self.assertEqual(result, "phone,email")

    def test_get_with_empty_key_returns_false(self):
        self.assertFalse(self.Preference.cositt_get_active_fields(""))
        self.assertFalse(self.Preference.cositt_get_active_fields(False))

    def test_set_with_empty_key_does_nothing(self):
        result = self.Preference.with_user(self.admin).cositt_set_active_fields("", "phone")
        self.assertFalse(result)
        self.assertEqual(
            self.Preference.with_user(self.admin).search_count([("view_key", "=", "")]), 0
        )

    # --- aislamiento por usuario --------------------------------------------

    def test_same_key_different_users_do_not_share_value(self):
        key = "res.partner,list,123,phone,email"
        self.Preference.with_user(self.admin).cositt_set_active_fields(key, "phone")
        self.Preference.with_user(self.other_user).cositt_set_active_fields(key, "email")

        self.assertEqual(
            self.Preference.with_user(self.admin).cositt_get_active_fields(key), "phone"
        )
        self.assertEqual(
            self.Preference.with_user(self.other_user).cositt_get_active_fields(key), "email"
        )

    def test_ordinary_user_does_not_see_others_records_via_search(self):
        key = "res.partner,list,123,phone,email"
        self.Preference.with_user(self.admin).cositt_set_active_fields(key, "phone")

        visible = self.Preference.with_user(self.other_user).search([
            ("user_id", "=", self.admin.id),
        ])

        self.assertFalse(visible)

    def test_admin_sees_all_records_via_search(self):
        key = "res.partner,list,123,phone,email"
        self.Preference.with_user(self.other_user).cositt_set_active_fields(key, "email")

        visible = self.Preference.with_user(self.admin).search([
            ("user_id", "=", self.other_user.id), ("view_key", "=", key),
        ])

        self.assertTrue(visible)

    # --- restricción de unicidad --------------------------------------------

    def test_unique_constraint_blocks_duplicate_user_and_key(self):
        key = "res.partner,list,123,phone,email"
        self.Preference.with_user(self.admin).create({
            "view_key": key, "active_fields": "phone",
        })
        with self.assertRaises(Exception):
            self.Preference.with_user(self.admin).create({
                "view_key": key, "active_fields": "email",
            })

    # --- código ------------------------------------------------------------

    def test_module_never_calls_sudo(self):
        module_dir = Path(__file__).resolve().parent.parent
        python_files = (module_dir / "models").glob("*.py")
        found = False
        for path in python_files:
            found = True
            self.assertNotIn(
                ".sudo(", path.read_text(encoding="utf-8"),
                "%s no debería usar sudo()" % path.name,
            )
        self.assertTrue(found)
