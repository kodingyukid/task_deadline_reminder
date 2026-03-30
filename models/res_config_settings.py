from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    task_reminder_email_from = fields.Char(
        string='Sender Email',
        help='Email address for sending task deadline reminders'
    )
    
    evolution_api_url = fields.Char(
        string='Evolution API URL',
        help='The URL of the Evolution API endpoint (e.g., https://sub.domain.com)'
    )
    
    evolution_api_key = fields.Char(
        string='Evolution API Key',
        help='API Key for Evolution API authentication'
    )
    
    evolution_instance_name = fields.Char(
        string='Evolution Instance Name',
        help='The instance name for Evolution API'
    )
    
    whatsapp_message_template = fields.Text(
        string='WhatsApp Message Template',
        help='Template for the WhatsApp message',
        default='Dear {user_name},\n\nThis is a reminder that the task "{task_name}" from project "{project_name}" is due on {deadline}.\n\nPlease ensure it is completed on time.\n\nThank you,\n{company_name}'
    )

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param(
            'task_deadline_reminder.task_reminder_email_from', self.task_reminder_email_from)
        self.env['ir.config_parameter'].sudo().set_param(
            'task_deadline_reminder.evolution_api_url', self.evolution_api_url)
        self.env['ir.config_parameter'].sudo().set_param(
            'task_deadline_reminder.evolution_api_key', self.evolution_api_key)
        self.env['ir.config_parameter'].sudo().set_param(
            'task_deadline_reminder.evolution_instance_name', self.evolution_instance_name)
        self.env['ir.config_parameter'].sudo().set_param(
            'task_deadline_reminder.whatsapp_message_template', self.whatsapp_message_template)

    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res.update(
            task_reminder_email_from=self.env['ir.config_parameter'].sudo().get_param(
                'task_deadline_reminder.task_reminder_email_from'),
            evolution_api_url=self.env['ir.config_parameter'].sudo().get_param(
                'task_deadline_reminder.evolution_api_url'),
            evolution_api_key=self.env['ir.config_parameter'].sudo().get_param(
                'task_deadline_reminder.evolution_api_key'),
            evolution_instance_name=self.env['ir.config_parameter'].sudo().get_param(
                'task_deadline_reminder.evolution_instance_name'),
            whatsapp_message_template=self.env['ir.config_parameter'].sudo().get_param(
                'task_deadline_reminder.whatsapp_message_template'),
        )
        return res
