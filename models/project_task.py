import logging
from odoo import models, api, fields
from odoo.exceptions import UserError
from datetime import date, timedelta

_logger = logging.getLogger(__name__)

class ProjectTask(models.Model):
    _inherit = 'project.task'

    @api.model
    def _test_send_deadline_reminder(self, test_email):
        _logger.info("--- Starting Task Deadline Reminder Test ---")
        if not test_email:
            _logger.warning("Test failed: No test email address provided.")
            raise UserError("Please select an employee to send the test email to.")

        _logger.info(f"Test email recipient: {test_email}")

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
            ('stage_id.fold', '=', False)
        ])

        for task in tasks:
            template = self.env.ref('task_deadline_reminder.email_template_task_deadline_reminder', raise_if_not_found=False)
            if template:
                email_values = {}
                if email_from:
                    email_values['email_from'] = email_from

                for user in task.user_ids:
                    if user.email:
                        email_values['email_to'] = user.email
                        template.send_mail(task.id, force_send=True, email_values=email_values)
