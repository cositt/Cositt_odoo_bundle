from pathlib import Path

from odoo.exceptions import UserError
from odoo.fields import Command
from odoo.tests.common import TransactionCase

CONFIG_PARAM = "cositt_attachment_lock.enabled"


class TestCosittAttachmentLock(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.thread = cls.env["res.partner"].create({"name": "Cliente de Prueba"})
        cls.admin = cls.env.ref("base.user_admin")

    def _set_enabled(self, value):
        self.env["ir.config_parameter"].sudo().set_param(CONFIG_PARAM, str(value))

    def _create_attachment(self, user=None, **extra):
        vals = {
            "name": "documento.txt",
            "res_model": "res.partner",
            "res_id": self.thread.id,
            "raw": b"contenido",
        }
        vals.update(extra)
        model = self.env["ir.attachment"].with_user(user) if user else self.env["ir.attachment"]
        return model.create(vals)

    def _make_ordinary_user(self):
        # Se reutiliza base.public_user (existente) en vez de crear un
        # res.users nuevo, porque res.users.create() falla bajo
        # --test-enable en este entorno (ver memoria del proyecto). Se
        # le AÑADE el grupo interno básico (sin tocar base.user_admin:
        # quitarle base.group_system dispara la validación propia de
        # Odoo "debe haber al menos un administrador", porque es el
        # único admin de esta base). public_user nunca tuvo
        # base.group_system ni el grupo de excepción, así que sirve tal
        # cual para simular un empleado normal sin privilegios.
        user = self.env.ref("base.public_user")
        # "Role / Public" y "Role / User" son grupos mutuamente
        # excluyentes (misma categoría de selección) -> hay que quitar
        # el primero al añadir el segundo, no basta con enlazar. Se
        # añade también group_partner_manager (permiso normal de
        # "gestión de contactos"): sin él, un group_user liso no tiene
        # ni siquiera acceso de escritura a res.partner en esta base
        # (ACL real comprobada al escribir los tests, no una suposición),
        # así que no podría crear el adjunto de prueba vinculado a un
        # contacto -- un caso de uso realista igualmente (cualquier
        # empleado que gestione contactos tiene este grupo).
        user.group_ids = [
            Command.unlink(self.env.ref("base.group_public").id),
            Command.link(self.env.ref("base.group_user").id),
            Command.link(self.env.ref("base.group_partner_manager").id),
        ]
        return user

    # --- datos cargados ---------------------------------------------------

    def test_config_parameter_seeded_disabled_by_default(self):
        value = self.env["ir.config_parameter"].sudo().get_param(CONFIG_PARAM)
        self.assertEqual(value, "False")

    def test_override_group_implied_by_group_system(self):
        group_system = self.env.ref("base.group_system")
        override_group = self.env.ref(
            "cositt_attachment_lock.group_cositt_attachment_lock_override"
        )
        self.assertIn(override_group.id, group_system.implied_ids.ids)

    # --- comportamiento con la protección desactivada (por defecto) -----

    def test_deletion_allowed_when_protection_disabled(self):
        self._set_enabled(False)
        user = self._make_ordinary_user()
        attachment = self._create_attachment(user=user)

        attachment.with_user(user).unlink()

        self.assertFalse(attachment.exists())

    # --- comportamiento con la protección activada -----------------------

    def test_ordinary_user_blocked_when_enabled(self):
        self._set_enabled(True)
        user = self._make_ordinary_user()
        attachment = self._create_attachment(user=user)

        with self.assertRaises(UserError) as capture:
            attachment.with_user(user).unlink()
        # No basta con "alguna UserError" (AccessError también lo es,
        # por herencia): se comprueba que es específicamente el mensaje
        # de este módulo, no un AccessError genérico de permisos.
        self.assertIn("protección", str(capture.exception))
        self.assertTrue(attachment.exists())

    def test_admin_can_delete_protected_attachment_when_enabled(self):
        self._set_enabled(True)
        attachment = self._create_attachment()

        # self.admin conserva su pertenencia por defecto a base.group_system
        # (no se ha tocado en este test) -> hereda el grupo de excepción.
        attachment.with_user(self.admin).unlink()

        self.assertFalse(attachment.exists())

    def test_orphan_attachment_without_res_model_not_protected(self):
        self._set_enabled(True)
        user = self._make_ordinary_user()
        attachment = self._create_attachment(user=user, res_model=False, res_id=False)

        attachment.with_user(user).unlink()

        self.assertFalse(attachment.exists())

    def test_attachment_with_res_field_not_protected(self):
        self._set_enabled(True)
        user = self._make_ordinary_user()
        # image_1920: campo Binary real de res.partner (no un nombre
        # inventado) -- con un res_field que no existe en el modelo, el
        # propio control de acceso de ir.attachment deniega el acceso
        # por su cuenta, sin llegar siquiera a la lógica de este módulo.
        attachment = self._create_attachment(user=user, res_field="image_1920")

        attachment.with_user(user).unlink()

        self.assertFalse(attachment.exists())

    def test_sudo_context_bypasses_protection(self):
        self._set_enabled(True)
        attachment = self._create_attachment()

        attachment.sudo().unlink()

        self.assertFalse(attachment.exists())

    def test_blocked_attempt_is_logged(self):
        self._set_enabled(True)
        user = self._make_ordinary_user()
        attachment = self._create_attachment(user=user)

        with self.assertLogs(
            "odoo.addons.cositt_attachment_lock.models.ir_attachment", level="WARNING"
        ) as capture:
            with self.assertRaises(UserError):
                attachment.with_user(user).unlink()
        self.assertTrue(
            any("Blocked deletion attempt" in message for message in capture.output)
        )

    # --- código ------------------------------------------------------------

    def test_module_only_uses_sudo_for_config_param(self):
        path = (
            Path(__file__).resolve().parent.parent / "models" / "ir_attachment.py"
        )
        content = path.read_text(encoding="utf-8")
        self.assertEqual(content.count(".sudo("), 1)
