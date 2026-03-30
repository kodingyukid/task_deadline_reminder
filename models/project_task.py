import logging
import requests
from datetime import datetime, timedelta
from odoo import fields, models, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class ProjectTask(models.Model):
    _inherit = 'project.task'

    reminder_method = fields.Selection([
        ('email', 'Email'),
        ('whatsapp', 'WhatsApp'),
        ('both', 'Email & WhatsApp')
    ], string='Reminder Method', default='email', help='Metode pengiriman reminder')

    def _cron_send_deadline_reminder(self):
        """
        Logika: Mencari tugas yang deadline-nya BESOK.
        Misal: Sekarang tgl 22, deadline tgl 23 -> Kirim Reminder.
        """
        # Menghitung tanggal besok berdasarkan waktu server saat ini
        tomorrow = datetime.now() + timedelta(days=1)
        tomorrow_str = tomorrow.strftime('%Y-%m-%d')
        
        _logger.info(f"Checking reminders for deadline: {tomorrow_str}")
        
        tasks = self.search([
            ('date_deadline', '=', tomorrow_str),
            ('reminder_method', 'in', ['email', 'whatsapp', 'both']),
            ('is_closed', '=', False) # Jangan kirim jika tugas sudah selesai
        ])
        
        for task in tasks:
            try:
                if task.reminder_method in ['email', 'both']:
                    task._send_email_reminder()
                if task.reminder_method in ['whatsapp', 'both']:
                    task._send_whatsapp_reminder()
            except Exception as e:
                _logger.error(f"Gagal mengirim reminder untuk task ID {task.id}: {str(e)}")

    def _format_whatsapp_number(self, number):
        """Logika mengubah 08xxx menjadi 628xxx dan hapus karakter non-digit"""
        if not number:
            return False
        
        # Hapus semua karakter selain angka (spasi, plus, minus)
        clean_number = "".join(filter(str.isdigit, number))
        
        # Jika dimulai dengan '08', ganti '0' di depan dengan '62'
        if clean_number.startswith('08'):
            clean_number = '62' + clean_number[1:]
        
        return clean_number

    def _send_whatsapp_reminder(self):
        """Mengirim pesan via Evolution API dengan link dinamis"""
        param_obj = self.env['ir.config_parameter'].sudo()
        
        # 1. Ambil Konfigurasi API
        evolution_url = param_obj.get_param('task_deadline_reminder.evolution_api_url', '').strip().rstrip('/')
        api_key = param_obj.get_param('task_deadline_reminder.evolution_api_key')
        instance_name = param_obj.get_param('task_deadline_reminder.evolution_instance_name')
        message_template = param_obj.get_param('task_deadline_reminder.whatsapp_message_template')

        if not all([evolution_url, api_key, instance_name, message_template]):
            _logger.warning("Konfigurasi WhatsApp Reminder belum lengkap di Settings.")
            return

        # 2. Buat Link Task (Dinamis sesuai domain ERP)
        base_url = param_obj.get_param('web.base.url').rstrip('/')
        task_link = f"{base_url}/web#id={self.id}&model=project.task&view_type=form"

        # 3. Kirim ke setiap User yang ditugaskan (Assignees)
        for user in self.user_ids:
            # Format nomor WA
            wa_number = self._format_whatsapp_number(user.mobile_phone or user.phone)
            
            if not wa_number:
                _logger.warning(f"User {user.name} tidak punya nomor HP yang valid.")
                continue
                
            try:
                # Isi variabel ke dalam template
                message = message_template.format(
                    user_name=user.name or 'Rekan',
                    task_name=self.name or 'N/A',
                    project_name=self.project_id.name if self.project_id else 'No Project',
                    deadline=self.date_deadline,
                    task_link=task_link,
                    company_name=self.company_id.name or 'Our Company'
                )

                payload = {
                    "number": wa_number,
                    "text": message
                }
                
                endpoint = f"{evolution_url}/message/sendText/{instance_name}"
                headers = {
                    'Content-Type': 'application/json',
                    'apikey': api_key
                }
                
                response = requests.post(endpoint, json=payload, headers=headers, timeout=25)
                
                if response.status_code in [200, 201]:
                    _logger.info(f"WA Reminder terkirim ke {wa_number} untuk task: {self.name}")
                else:
                    _logger.error(f"Evolution API Error {response.status_code}: {response.text}")

            except Exception as e:
                _logger.error(f"Terjadi kesalahan saat kirim WA ke {user.name}: {str(e)}")

    def _send_email_reminder(self):
        """Kirim email menggunakan template XML"""
        template = self.env.ref('task_deadline_reminder.email_template_task_deadline_reminder', raise_if_not_found=False)
        if not template:
            return
            
        email_from = self.env['ir.config_parameter'].sudo().get_param('task_deadline_reminder.task_reminder_email_from')
        
        for user in self.user_ids:
            if user.email:
                template.send_mail(self.id, force_send=True, email_values={
                    'email_to': user.email,
                    'email_from': email_from
                })