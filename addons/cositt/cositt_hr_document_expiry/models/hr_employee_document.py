import logging
from datetime import timedelta

from odoo import api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


def _document_expiry_state(expiry_date, reminder_days_before, today):
    """Función pura: decide el estado de un documento a partir de fechas
    ya planas, para poder testearla sin depender del reloj real."""
    if not expiry_date:
        return "valid"
    alert_date = expiry_date - timedelta(days=reminder_days_before or 0)
    if expiry_date < today:
        return "expired"
    if alert_date <= today:
        return "expiring_soon"
    return "valid"


class HrEmployeeDocument(models.Model):
    _name = "hr.employee.document"
    _description = "Employee document with expiry tracking"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    employee_id = fields.Many2one(
        "hr.employee", required=True, ondelete="cascade", index=True
    )
    name = fields.Char(required=True, help="E.g. DNI, work permit, driving licence")
    expiry_date = fields.Date(required=True)
    reminder_days_before = fields.Integer(
        default=30,
        help="How many days before expiry to raise a reminder activity",
    )
    alert_date = fields.Date(compute="_compute_alert_date", store=True)
    state = fields.Selection(
        [
            ("valid", "Valid"),
            ("expiring_soon", "Expiring soon"),
            ("expired", "Expired"),
        ],
        compute="_compute_state",
    )
    active = fields.Boolean(default=True)

    @api.depends("expiry_date", "reminder_days_before")
    def _compute_alert_date(self):
        for document in self:
            if document.expiry_date:
                document.alert_date = document.expiry_date - timedelta(
                    days=document.reminder_days_before or 0
                )
            else:
                document.alert_date = False

    @api.depends("expiry_date", "reminder_days_before")
    def _compute_state(self):
        today = fields.Date.context_today(self)
        for document in self:
            document.state = _document_expiry_state(
                document.expiry_date, document.reminder_days_before, today
            )

    @api.constrains("reminder_days_before")
    def _check_reminder_days_before(self):
        for document in self:
            if document.reminder_days_before is not False and document.reminder_days_before < 0:
                raise ValidationError(
                    self.env._("Reminder days before expiry cannot be negative.")
                )

    def _get_reminder_responsible(self):
        self.ensure_one()
        employee = self.employee_id
        return employee.user_id or employee.parent_id.user_id

    @api.model
    def _cron_check_expiring_documents(self):
        today = fields.Date.context_today(self)
        todo_activity_type = self.env.ref("mail.mail_activity_data_todo")
        due_documents = self.search([("alert_date", "<=", today)])
        for document in due_documents:
            already_reminded = document.activity_ids.filtered(
                lambda a: a.activity_type_id == todo_activity_type
            )
            if already_reminded:
                continue

            responsible = document._get_reminder_responsible()
            if not responsible:
                _logger.warning(
                    "No se pudo asignar el recordatorio de caducidad del "
                    "documento '%s' (id=%s): el empleado %s no tiene "
                    "usuario ni responsable con usuario.",
                    document.name,
                    document.id,
                    document.employee_id.display_name,
                )
                continue

            document.activity_schedule(
                "mail.mail_activity_data_todo",
                date_deadline=document.expiry_date,
                summary=self.env._(
                    "Document expiring: %(name)s (%(employee)s)",
                    name=document.name,
                    employee=document.employee_id.display_name,
                ),
                user_id=responsible.id,
            )


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    document_ids = fields.One2many("hr.employee.document", "employee_id", string="Documents")
