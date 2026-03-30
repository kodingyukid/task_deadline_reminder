import logging
import json
from datetime import datetime, timedelta
from odoo import fields, models, api
from odoo.exceptions import UserError
import requests

_logger = logging.getLogger(__name__)


class ProjectTask(models.Model):
    _inherit = 'project.task'

    reminder_method = fields.Selection([
        ('email', 'Email'),
        ('whatsapp', 'WhatsApp'),
        ('both', 'Email & WhatsApp')
    ], string='Reminder Method', default='email', help='Choose how to send deadline reminders')

    def _cron_send_deadline_reminder(self):
        """Send deadline reminders for tasks approaching deadline"""
        tomorrow = datetime.now() + timedelta(days=1)
        tomorrow_str = tomorrow.strftime('%Y-%m-%d')
        
        tasks = self.search([
            ('date_deadline', '=', tomorrow_str),
            ('reminder_method', 'in', ['email', 'whatsapp', 'both'])
        ])
        
        for task in tasks:
            try:
                if task.reminder_method in ['email', 'both']:
                    task._send_email_reminder()
                if task.reminder_method in ['whatsapp', 'both']:
                    task._send_whatsapp_reminder()
            except Exception as e:
                _logger.error(f"Failed to send reminder for task {task.id}: {str(e)}")

    def _send_email_reminder(self):
        """Send email reminder"""
        if not self.user_ids:
            _logger.warning(f"No user assigned to task {self.id}")
            return
            
        template = self.env.ref('task_deadline_reminder.email_template_task_deadline_reminder')
        for user in self.user_ids:
            try:
                template.send_mail(self.id, force_send=True, email_values={
                    'email_to': user.email,
                    'email_from': self.env['ir.config_parameter'].sudo().get_param(
                        'task_deadline_reminder.task_reminder_email_from')
                })
                _logger.info(f"Email reminder sent to {user.email} for task {self.name}")
            except Exception as e:
                _logger.error(f"Failed to send email to {user.email}: {str(e)}")

    def _send_whatsapp_reminder(self):
        """Send WhatsApp reminder using Evolution API"""
        evolution_url = self.env['ir.config_parameter'].sudo().get_param(
            'task_deadline_reminder.evolution_api_url')
        api_key = self.env['ir.config_parameter'].sudo().get_param(
            'task_deadline_reminder.evolution_api_key')
        instance_name = self.env['ir.config_parameter'].sudo().get_param(
            'task_deadline_reminder.evolution_instance_name')
        
        if not all([evolution_url, api_key, instance_name]):
            _logger.warning("Evolution API configuration is incomplete")
            return
            
        if not self.user_ids:
            _logger.warning(f"No user assigned to task {self.id}")
            return
            
        message_template = self.env['ir.config_parameter'].sudo().get_param(
            'task_deadline_reminder.whatsapp_message_template')
        
        for user in self.user_ids:
            if not user.mobile_phone:
                _logger.warning(f"No mobile phone for user {user.name}")
                continue
                
            try:
                # Format message
                message = message_template.format(
                    user_name=user.name,
                    task_name=self.name,
                    project_name=self.project_id.name if self.project_id else 'N/A',
                    deadline=self.date_deadline,
                    company_name=self.company_id.name
                )
                
                # Prepare Evolution API payload
                payload = {
                    "number": user.mobile_phone,
                    "text": message
                }
                
                # Make API request
                endpoint = f"{evolution_url}/message/sendText/{instance_name}"
                headers = {
                    'Content-Type': 'application/json',
                    'apikey': api_key
                }
                
                response = requests.post(
                    endpoint,
                    json=payload,
                    headers=headers,
                    timeout=30
                )
                
                if response.status_code == 200:
                    _logger.info(f"WhatsApp reminder sent to {user.mobile_phone} for task {self.name}")
                else:
                    _logger.error(f"Evolution API error: {response.status_code} - {response.text}")
                    
            except Exception as e:
                _logger.error(f"Failed to send WhatsApp to {user.mobile_phone}: {str(e)}")

    def _test_send_deadline_reminder(self, test_email):
        """Test function for sending deadline reminder"""
        try:
            template = self.env.ref('task_deadline_reminder.email_template_task_deadline_reminder')
            template.send_mail(self.id, force_send=True, email_values={
                'email_to': test_email,
                'email_from': self.env['ir.config_parameter'].sudo().get_param(
                    'task_deadline_reminder.task_reminder_email_from')
            })
            _logger.info(f"Test email sent to {test_email}")
        except Exception as e:
            _logger.error(f"Failed to send test email: {str(e)}")
            raise UserError(f"Failed to send test email: {str(e)}")
