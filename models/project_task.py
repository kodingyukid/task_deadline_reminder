import logging
from odoo import models, api, fields
from odoo.exceptions import UserError
from datetime import date, timedelta
import requests
import json

_logger = logging.getLogger(__name__)

class ProjectTask(models.Model):
    _inherit = 'project.task'

    reminder_method = fields.Selection([
        ('email', 'Email'),
        ('whatsapp', 'WhatsApp'),
        ('both', 'Both')
    ], string='Reminder Method', default='email')

    last_reminder_date = fields.Date(string='Last Reminder Date', help='Date when the last reminder was sent.')

    @api.model
    def _test_send_deadline_reminder(self, test_email):
        # ... (rest of the method unchanged, but ensuring I don't break indentation or missing lines in replacement)
        # To avoid replacing the whole file, I will split this into two replacement chunks if possible, 
        # OR I will just replace the fields area and then the cron area.
        # However, the user wants me to fix the spam issue.
        # Let's use MultiReplace or just replace the specific parts.
        # I'll replace the fields definition first.
        pass # Placeholder for valid python syntax in this thought block

    # I will split this tool call into two: one for field, one for cron logic.


    @api.model
    def _test_send_deadline_reminder(self, test_email):
        _logger.info("--- Starting Task Deadline Reminder Test ---")
        if not test_email:
            _logger.warning("Test failed: No test email address provided.")
            raise UserError("Please select an employee to send the test email to.")

        _logger.info(f"Test email recipient: {test_email}")

        # Test WhatsApp
        waha_url = self.env['ir.config_parameter'].sudo().get_param('task_deadline_reminder.waha_api_url')
        if waha_url:
            self._send_whatsapp_message("Test Task", date.today(), "http://localhost:8069", test_email)

        today = date.today()
        reminder_dates = [
            today,
            today + timedelta(days=1),
            today + timedelta(days=3)
        ]
        _logger.info(f"Searching for tasks with deadlines on: {reminder_dates}")

        task = self.search([
            ('date_deadline', 'in', reminder_dates),
            ('user_ids', '!=', False),
            ('stage_id.fold', '=', False)
        ], order='create_date desc', limit=1)

        if not task:
            _logger.warning("Test Failed: No suitable task found.")
            raise UserError("Test Failed: No open task found with a deadline set for today, tomorrow, or in 3 days. Please create one to run the test.")

        _logger.info(f"Task found: '{task.name}' (ID: {task.id})")

        template = self.env.ref('task_deadline_reminder.email_template_task_deadline_reminder', raise_if_not_found=False)
        if template:
            _logger.info("Email template found. Preparing to send email.")
            mail_server_id = self.env['ir.config_parameter'].sudo().get_param('task_deadline_reminder.email_from')
            email_from = False
            if mail_server_id:
                mail_server = self.env['ir.mail_server'].browse(int(mail_server_id))
                if mail_server.smtp_user:
                    email_from = mail_server.smtp_user
            
            _logger.info(f"Sender email configured: {email_from or 'Default'}")

            email_values = {'email_to': test_email}
            if email_from:
                email_values['email_from'] = email_from
            
            template.send_mail(task.id, force_send=True, email_values=email_values)
            _logger.info(f"Successfully called send_mail for task ID {task.id} to {test_email}.")
        else:
            _logger.error("Email template 'email_template_task_deadline_reminder' not found.")
        
        _logger.info("--- Finished Task Deadline Reminder Test ---")

    def _send_whatsapp_message(self, task_name, deadline, task_link, phone_number):
        waha_url = self.env['ir.config_parameter'].sudo().get_param('task_deadline_reminder.waha_api_url')
        template = self.env['ir.config_parameter'].sudo().get_param('task_deadline_reminder.whatsapp_message_template')
        
        if not waha_url:
            _logger.warning("WAHA API URL is not configured.")
            return

        if not phone_number:
            _logger.warning("No phone number provided for WhatsApp reminder.")
            return

        message = template.replace('{{ task_name }}', task_name)\
                          .replace('{{ deadline }}', str(deadline))\
                          .replace('{{ task_link }}', task_link)

        headers = {'Content-Type': 'application/json'}
        payload = {
            'chatId': f"{phone_number}@c.us",
            'text': message,
            'session': 'default'
        }

        try:
            response = requests.post(f"{waha_url}/api/sendText", headers=headers, data=json.dumps(payload))
            if response.status_code == 200:
                _logger.info(f"WhatsApp message sent to {phone_number}")
            else:
                _logger.error(f"Failed to send WhatsApp message. Status: {response.status_code}, Response: {response.text}")
        except Exception as e:
            _logger.error(f"Error sending WhatsApp message: {str(e)}")

    @api.model
    def _cron_send_deadline_reminder(self):
        today = date.today()
        reminder_dates = [
            today,
            today + timedelta(days=1),
            today + timedelta(days=3)
        ]

        tasks = self.search([
            ('date_deadline', 'in', reminder_dates),
            ('user_ids', '!=', False),
            ('stage_id.fold', '=', False),
            '|', ('last_reminder_date', '=', False), ('last_reminder_date', '!=', today)
        ])
        
        mail_server_id = self.env['ir.config_parameter'].sudo().get_param('task_deadline_reminder.email_from')
        email_from = False
        if mail_server_id:
            mail_server = self.env['ir.mail_server'].browse(int(mail_server_id))
            if mail_server.smtp_user:
                email_from = mail_server.smtp_user

        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')

        for task in tasks:
            method = task.reminder_method
            reminder_sent = False
            
            # Email Logic
            if method in ['email', 'both']:
                template = self.env.ref('task_deadline_reminder.email_template_task_deadline_reminder', raise_if_not_found=False)
                if template:
                    email_values = {}
                    if email_from:
                        email_values['email_from'] = email_from

                    for user in task.user_ids:
                        if user.email:
                            email_values['email_to'] = user.email
                            template.send_mail(task.id, force_send=True, email_values=email_values)
                            reminder_sent = True

            # WhatsApp Logic
            if method in ['whatsapp', 'both']:
                for user in task.user_ids:
                    # Check for 'mobile' or 'phone' in Partner
                    phone = user.partner_id.mobile or user.partner_id.phone
                    if phone:
                        # Clean phone number logic could go here (remove +, spaces, etc if needed by WAHA)
                        # Assuming WAHA takes number as is or clean enough
                        task_link = f"{base_url}/web#id={task.id}&model=project.task&view_type=form"
                        self._send_whatsapp_message(task.name, task.date_deadline, task_link, phone)
                        reminder_sent = True
                    else:
                        _logger.warning(f"User {user.name} has no mobile/phone for WhatsApp reminder.")
            
            if reminder_sent:
                task.write({'last_reminder_date': today})