from odoo import fields, models, api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    task_reminder_email_from = fields.Many2one(
        'ir.mail_server',
        string='Reminder Email From',
        config_parameter='task_deadline_reminder.email_from',
        help="The email address to be used as the 'from' address for task deadline reminders."
    )

