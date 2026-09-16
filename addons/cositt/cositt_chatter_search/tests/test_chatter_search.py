from pathlib import Path

from odoo.exceptions import AccessError
from odoo.tests.common import TransactionCase


class TestCosittChatterSearch(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.thread = cls.env["res.partner"].create({"name": "Cliente de Prueba"})
        cls.author_juan = cls.env["res.partner"].create({"name": "Juan Pérez"})
        cls.author_maria = cls.env["res.partner"].create({"name": "Maria Lopez"})

    def _post(self, author_id=False, email_from=False, author_guest_id=False,
              body="contenido de prueba", subject=False):
        return self.env["mail.message"].create({
            "model": "res.partner",
            "res_id": self.thread.id,
            "message_type": "comment",
            "body": body,
            "subject": subject,
            "author_id": author_id,
            "email_from": email_from,
            "author_guest_id": author_guest_id,
        })

    def _fetch(self, **kwargs):
        return self.env["mail.message"]._message_fetch(
            domain=None, thread=self.thread, **kwargs
        )

    # --- búsqueda por autor: el único añadido de este módulo -----------

    def test_search_by_author_name_matches_only_that_authors_messages(self):
        msg_juan = self._post(author_id=self.author_juan.id, body="informe mensual")
        msg_maria = self._post(author_id=self.author_maria.id, body="informe mensual")

        res = self._fetch(search_term="Juan")

        self.assertIn(msg_juan.id, res["messages"].ids)
        self.assertNotIn(msg_maria.id, res["messages"].ids)

    def test_search_by_email_from_matches_message_without_author(self):
        msg = self._post(email_from="ventas@externo.example", body="pedido enviado")

        res = self._fetch(search_term="externo")

        self.assertIn(msg.id, res["messages"].ids)

    def test_search_by_guest_name_matches_message(self):
        guest = self.env["mail.guest"].create({"name": "Visitante Anonimo"})
        msg = self._post(author_guest_id=guest.id, body="consulta desde el portal")

        res = self._fetch(search_term="Anonimo")

        self.assertIn(msg.id, res["messages"].ids)

    def test_search_by_author_does_not_match_unrelated_term(self):
        self._post(author_id=self.author_juan.id, body="informe mensual")

        res = self._fetch(search_term="palabra_que_no_aparece_en_nada")

        self.assertEqual(len(res["messages"]), 0)

    # --- regresión: el resto del comportamiento nativo no cambia --------

    def test_search_still_matches_body_like_before(self):
        msg = self._post(body="contenido especial xyz")

        res = self._fetch(search_term="especial")

        self.assertIn(msg.id, res["messages"].ids)

    def test_search_still_matches_subject(self):
        msg = self._post(body="cuerpo genérico", subject="Asunto Particular")

        res = self._fetch(search_term="Particular")

        self.assertIn(msg.id, res["messages"].ids)

    def test_no_search_term_skips_count_like_before(self):
        self._post(author_id=self.author_juan.id)

        res = self._fetch()

        self.assertNotIn("count", res)

    def test_search_respects_limit_and_reports_total_count(self):
        self._post(author_id=self.author_juan.id, body="msg 1")
        self._post(author_id=self.author_juan.id, body="msg 2")

        res = self._fetch(search_term="Juan", limit=1)

        self.assertEqual(res["count"], 2)
        self.assertEqual(len(res["messages"]), 1)

    # --- permisos: sin sudo nuevo, respeta acceso al hilo ----------------

    def test_search_excludes_messages_of_thread_without_access(self):
        restricted_group = self.env["res.groups"].create(
            {"name": "Cositt Chatter Search - grupo restringido (test)"}
        )
        self.env["ir.rule"].create({
            "name": "Bloqueo total de prueba",
            "model_id": self.env["ir.model"]._get("res.partner").id,
            "groups": [(6, 0, [restricted_group.id])],
            "domain_force": "[('id', '=', False)]",
        })
        msg = self._post(author_id=self.author_juan.id, body="confidencial")
        public_user = self.env.ref("base.public_user")
        public_user.group_ids = [(4, restricted_group.id)]

        res = self.env["mail.message"].with_user(public_user)._message_fetch(
            domain=None, thread=self.thread, search_term="confidencial"
        )

        self.assertNotIn(msg.id, res["messages"].ids)

    def test_module_only_uses_sudo_inherited_or_justified(self):
        # Este override es una copia completa de mail.message._message_fetch
        # del core (ver comentario en el propio archivo): 2 usos de sudo()
        # ya estaban en el original (nombre de adjunto y valores de
        # tracking). El añadido de este módulo suma 2 más (nombre de autor,
        # nombre de invitado), con el mismo criterio ya documentado por el
        # core: el acceso real lo decide el search() final de mail.message,
        # sin sudo. Se verifica el número exacto (4) en vez de "cero" como
        # en el resto de plugins, precisamente porque aquí sí hay sudo
        # heredado y legítimo, cada uno con su comentario justificándolo.
        path = (
            Path(__file__).resolve().parent.parent / "models" / "mail_message.py"
        )
        content = path.read_text(encoding="utf-8")
        self.assertEqual(content.count(".sudo("), 4)
        self.assertIn("# sudo:", content)

    def test_module_never_raises_unrelated_access_error(self):
        # Complemento del test de permisos: una búsqueda normal (con
        # acceso) no debe lanzar AccessError.
        try:
            self._fetch(search_term="Juan")
        except AccessError:
            self.fail("_message_fetch no debería lanzar AccessError con acceso normal")
