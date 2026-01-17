from odoo import fields, models, api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    task_reminder_email_from = fields.Many2one(
        'ir.mail_server',
        string='Reminder Email From',
        config_parameter='task_deadline_reminder.email_from',
        help="The email address to be used as the 'from' address for task deadline reminders."
    )

    waha_api_url = fields.Char(
        string='WAHA API URL',
        config_parameter='task_deadline_reminder.waha_api_url',
        help="The URL of the WAHA API endpoint (e.g., http://localhost:3000)."
    )
    
    whatsapp_message_template = fields.Char(
        string='WhatsApp Message Template',
        config_parameter='task_deadline_reminder.whatsapp_message_template',
        default="Reminder: Task '{{ task_name }}' is due on {{ deadline }}. Link: {{ task_link }}. Do not reply.",
        help="Template for the WhatsApp message. Variables: {{ task_name }}, {{ deadline }}, {{ task_link }}."
    )

