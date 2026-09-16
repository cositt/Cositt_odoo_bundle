from datetime import timedelta
from pathlib import Path

from odoo.exceptions import AccessError, UserError
from odoo.fields import Date
from odoo.tests.common import TransactionCase


class TestCosittActivityDigest(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Cliente de Prueba"})
        cls.todo_type = cls.env.ref("mail.mail_activity_data_todo")

    def _schedule_activity(self, record, days_from_today=0, summary="Actividad de prueba"):
        return record.activity_schedule(
            "mail.mail_activity_data_todo",
            summary=summary,
            date_deadline=Date.today() + timedelta(days=days_from_today),
        )

    # --- datos cargados --------------------------------------------------

    def test_module_data_loaded(self):
        menu = self.env.ref("cositt_activity_digest.menu_cositt_activity_digest_root")
        self.assertEqual(menu.action.res_model, "mail.activity")
        action = self.env.ref(
            "cositt_activity_digest.action_cositt_activity_postpone_wizard"
        )
        self.assertEqual(action.model_id.model, "mail.activity")
        access = self.env.ref(
            "cositt_activity_digest.access_cositt_activity_postpone_wizard_user"
        )
        self.assertTrue(access.perm_create)

    # --- apertura del wizard ---------------------------------------------

    def test_open_wizard_requires_selection(self):
        with self.assertRaises(UserError):
            self.env["mail.activity"].cositt_action_open_postpone_wizard()

    def test_open_wizard_passes_selected_activities_as_default(self):
        activity = self._schedule_activity(self.partner)
        action = activity.cositt_action_open_postpone_wizard()
        self.assertEqual(action["res_model"], "cositt.activity.postpone.wizard")
        self.assertEqual(
            action["context"]["default_activity_ids"], [(6, 0, [activity.id])]
        )

    # --- posponer ----------------------------------------------------------

    def test_postpone_shifts_deadline_forward(self):
        activity = self._schedule_activity(self.partner, days_from_today=0)
        original_deadline = activity.date_deadline
        wizard = self.env["cositt.activity.postpone.wizard"].create({
            "activity_ids": [(6, 0, [activity.id])],
            "days": 3,
        })

        wizard.action_postpone()

        self.assertEqual(activity.date_deadline, original_deadline + timedelta(days=3))

    def test_postpone_negative_days_brings_deadline_forward_in_time(self):
        # "days" negativo adelanta la actividad en vez de posponerla.
        activity = self._schedule_activity(self.partner, days_from_today=5)
        original_deadline = activity.date_deadline
        wizard = self.env["cositt.activity.postpone.wizard"].create({
            "activity_ids": [(6, 0, [activity.id])],
            "days": -2,
        })

        wizard.action_postpone()

        self.assertEqual(activity.date_deadline, original_deadline - timedelta(days=2))

    def test_postpone_applies_to_all_selected_activities(self):
        other_partner = self.env["res.partner"].create({"name": "Otro Cliente"})
        activity_a = self._schedule_activity(self.partner, summary="A")
        activity_b = self._schedule_activity(other_partner, summary="B")
        deadline_a = activity_a.date_deadline
        deadline_b = activity_b.date_deadline
        wizard = self.env["cositt.activity.postpone.wizard"].create({
            "activity_ids": [(6, 0, [activity_a.id, activity_b.id])],
            "days": 2,
        })

        wizard.action_postpone()

        self.assertEqual(activity_a.date_deadline, deadline_a + timedelta(days=2))
        self.assertEqual(activity_b.date_deadline, deadline_b + timedelta(days=2))

    def test_activity_count_computed(self):
        activity_a = self._schedule_activity(self.partner, summary="A")
        activity_b = self._schedule_activity(self.partner, summary="B")
        wizard = self.env["cositt.activity.postpone.wizard"].create({
            "activity_ids": [(6, 0, [activity_a.id, activity_b.id])],
        })
        self.assertEqual(wizard.activity_count, 2)

    def test_postpone_requires_nonzero_days(self):
        activity = self._schedule_activity(self.partner)
        wizard = self.env["cositt.activity.postpone.wizard"].create({
            "activity_ids": [(6, 0, [activity.id])],
            "days": 0,
        })
        with self.assertRaises(UserError):
            wizard.action_postpone()

    def test_postpone_requires_at_least_one_activity(self):
        wizard = self.env["cositt.activity.postpone.wizard"].create({"days": 1})
        with self.assertRaises(UserError):
            wizard.action_postpone()

    # --- permisos: sin sudo, respeta record rules -------------------------

    def test_respects_record_rules_without_sudo(self):
        # No se crea un res.users nuevo (res.users.create() falla en este
        # entorno bajo --test-enable por un problema de entorno ajeno a
        # este módulo — ver memoria de sesión / cositt_pdf_merge), y
        # base.public_user no sirve aquí: al no tener base.group_user
        # fallaría por el ACL del propio wizard, no por el ir.rule que
        # queremos probar. Se usa base.user_admin (usuario ya existente,
        # confirmado NO superusuario real en este entorno — a diferencia
        # de self.env.user dentro de un test, que sí lo es y bypassa
        # ir.rule por definición) con un grupo restringido temporal.
        restricted_group = self.env["res.groups"].create(
            {"name": "Cositt Activity Digest - grupo restringido (test)"}
        )
        self.env["ir.rule"].create({
            "name": "Bloqueo total de prueba",
            "model_id": self.env["ir.model"]._get("res.partner").id,
            "groups": [(6, 0, [restricted_group.id])],
            "domain_force": "[('id', '=', False)]",
        })
        activity = self._schedule_activity(self.partner)
        original_deadline = activity.date_deadline
        restricted_admin = self.env.ref("base.user_admin")
        restricted_admin.group_ids = [(4, restricted_group.id)]

        # mail.activity delega en el registro vinculado (res.partner):
        # escribir directamente sobre ella como el usuario restringido
        # debe fallar con AccessError, sin sudo() en ningún punto.
        with self.assertRaises(AccessError):
            activity.with_user(restricted_admin).write(
                {"date_deadline": original_deadline + timedelta(days=1)}
            )

        # Doble comprobación a través del propio asistente: el Many2many
        # `activity_ids` filtra en silencio (comportamiento estándar de
        # Odoo en campos relacionales, no un fallo de este módulo) en
        # vez de lanzar un error — así que el asistente cae en su propia
        # validación de "sin actividades", y en cualquier caso la fecha
        # de la actividad ajena no se modifica.
        wizard = self.env["cositt.activity.postpone.wizard"].create({
            "activity_ids": [(6, 0, [activity.id])],
            "days": 1,
        })
        with self.assertRaises(UserError):
            wizard.with_user(restricted_admin).action_postpone()
        self.assertEqual(activity.date_deadline, original_deadline)

    def test_module_never_calls_sudo(self):
        module_dir = Path(__file__).resolve().parent.parent
        python_files = [
            *(module_dir / "models").glob("*.py"),
            *(module_dir / "wizard").glob("*.py"),
        ]
        self.assertTrue(python_files)
        for path in python_files:
            self.assertNotIn(
                ".sudo(", path.read_text(encoding="utf-8"),
                "%s no debería usar sudo()" % path.name,
            )
