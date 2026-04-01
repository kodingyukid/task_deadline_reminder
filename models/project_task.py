import logging
import requests
from datetime import datetime, time, timedelta

import pytz

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

    def _cron_domain_deadline_tomorrow(self):
        """
        Odoo 17: project.task.date_deadline bertipe Datetime (bukan Date).
        Domain ('date_deadline', '=', tanggal) hanya cocok nilai persis tengah malam,
        sehingga deadline 02/04 10:00 tidak ketemu. Pakai rentang [start, end) hari
        'besok' dalam timezone user cron, lalu konversi ke UTC (format DB Odoo).
        """
        tz_name = self.env.user.tz or 'UTC'
        try:
            tz = pytz.timezone(tz_name)
        except Exception:
            tz = pytz.UTC
            tz_name = 'UTC'
        today = fields.Date.context_today(self)
        tomorrow = today + timedelta(days=1)
        start_local = tz.localize(datetime.combine(tomorrow, time.min))
        end_local = start_local + timedelta(days=1)
        start_utc = start_local.astimezone(pytz.UTC).replace(tzinfo=None)
        end_utc = end_local.astimezone(pytz.UTC).replace(tzinfo=None)
        return [
            ('date_deadline', '>=', start_utc),
            ('date_deadline', '<', end_utc),
        ], {
            'tz': tz_name,
            'today': today,
            'tomorrow_cal': tomorrow,
            'start_utc': start_utc,
            'end_utc': end_utc,
        }

    def _cron_send_deadline_reminder(self):
        """
        Logika: Mencari tugas yang deadline-nya BESOK.
        Misal: Sekarang tgl 22, deadline tgl 23 -> Kirim Reminder.
        """
        deadline_dom, meta = self._cron_domain_deadline_tomorrow()

        _logger.info(
            "[task_deadline_reminder] === Cron: kirim reminder deadline ==="
        )
        _logger.info(
            "[task_deadline_reminder] Konteks: user_cron=%s (id=%s) | tz=%s | "
            "hari_ini=%s | besok(kalender)=%s",
            self.env.user.login,
            self.env.user.id,
            meta['tz'],
            meta['today'],
            meta['tomorrow_cal'],
        )
        _logger.info(
            "[task_deadline_reminder] Pencarian date_deadline (Datetime): "
            "UTC [%s .. %s) (semua jam di hari besok menurut tz di atas)",
            meta['start_utc'],
            meta['end_utc'],
        )
        _logger.info(
            "[task_deadline_reminder] Syarat lain: reminder_method [email, whatsapp, both]; "
            "stage kosong ATAU stage.fold = False.",
        )

        tasks = self.search(
            deadline_dom
            + [
                ('reminder_method', 'in', ['email', 'whatsapp', 'both']),
                '|',
                ('stage_id', '=', False),
                ('stage_id.fold', '=', False),
            ]
        )

        _logger.info(
            "[task_deadline_reminder] Hasil pencarian: %s task(s) cocok.",
            len(tasks),
        )
        if not tasks:
            _logger.info(
                "[task_deadline_reminder] Tidak ada task. Periksa: deadline (tanggal+waktu) jatuh di hari %s "
                "(lihat rentang UTC di atas); metode reminder; tahapan tidak folded.",
                meta['tomorrow_cal'],
            )
            _logger.info("[task_deadline_reminder] === Cron selesai (tanpa pengiriman) ===")
            return

        for task in tasks:
            _logger.info(
                "[task_deadline_reminder] --- Task id=%s | nama=%r | metode=%s | stage=%s | fold=%s ---",
                task.id,
                task.name,
                task.reminder_method,
                task.stage_id.display_name if task.stage_id else '(tanpa stage)',
                task.stage_id.fold if task.stage_id else False,
            )
            try:
                if task.reminder_method in ['email', 'both']:
                    _logger.info(
                        "[task_deadline_reminder] Task id=%s: jalankan pengiriman EMAIL",
                        task.id,
                    )
                    task._send_email_reminder()
                if task.reminder_method in ['whatsapp', 'both']:
                    _logger.info(
                        "[task_deadline_reminder] Task id=%s: jalankan pengiriman WHATSAPP",
                        task.id,
                    )
                    task._send_whatsapp_reminder()
                _logger.info(
                    "[task_deadline_reminder] Task id=%s: selesai tanpa error",
                    task.id,
                )
            except Exception as e:
                _logger.exception(
                    "[task_deadline_reminder] Gagal mengirim reminder untuk task id=%s: %s",
                    task.id,
                    str(e),
                )
        _logger.info("[task_deadline_reminder] === Cron selesai ===")

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
            _logger.warning(
                "[task_deadline_reminder] Task id=%s: konfigurasi WhatsApp belum lengkap "
                "(Evolution URL / API Key / Instance / template). Cek Settings.",
                self.id,
            )
            return

        # 2. Buat Link Task (Dinamis sesuai domain ERP)
        base_url = param_obj.get_param('web.base.url').rstrip('/')
        task_link = f"{base_url}/web#id={self.id}&model=project.task&view_type=form"

        # 3. Kirim ke setiap User yang ditugaskan (Assignees)
        if not self.user_ids:
            _logger.warning(
                "[task_deadline_reminder] Task id=%s: tidak ada assignee (user_ids kosong), WA tidak dikirim.",
                self.id,
            )
            return

        for user in self.user_ids:
            # Format nomor WA
            wa_number = self._format_whatsapp_number(user.mobile_phone or user.phone)
            
            if not wa_number:
                _logger.warning(
                    "[task_deadline_reminder] Task id=%s: user %s (id=%s) tidak punya nomor HP yang valid.",
                    self.id,
                    user.name,
                    user.id,
                )
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
                    _logger.info(
                        "[task_deadline_reminder] Task id=%s: WA terkirim ke %s (user=%s)",
                        self.id,
                        wa_number,
                        user.name,
                    )
                else:
                    _logger.error(
                        "[task_deadline_reminder] Task id=%s: Evolution API HTTP %s | %s",
                        self.id,
                        response.status_code,
                        response.text,
                    )

            except Exception as e:
                _logger.exception(
                    "[task_deadline_reminder] Task id=%s: error kirim WA ke user %s: %s",
                    self.id,
                    user.name,
                    str(e),
                )

    def _send_email_reminder(self):
        """Kirim email menggunakan template XML"""
        template = self.env.ref('task_deadline_reminder.email_template_task_deadline_reminder', raise_if_not_found=False)
        if not template:
            _logger.warning(
                "[task_deadline_reminder] Task id=%s: template email tidak ditemukan, tidak mengirim.",
                self.id,
            )
            return

        if not self.user_ids:
            _logger.warning(
                "[task_deadline_reminder] Task id=%s: tidak ada assignee, email tidak dikirim.",
                self.id,
            )
            return

        email_from = self.env['ir.config_parameter'].sudo().get_param('task_deadline_reminder.task_reminder_email_from')
        sent = 0
        for user in self.user_ids:
            if user.email:
                template.send_mail(self.id, force_send=True, email_values={
                    'email_to': user.email,
                    'email_from': email_from
                })
                sent += 1
                _logger.info(
                    "[task_deadline_reminder] Task id=%s: email reminder dikirim ke %s (user=%s)",
                    self.id,
                    user.email,
                    user.name,
                )
            else:
                _logger.warning(
                    "[task_deadline_reminder] Task id=%s: user %s (id=%s) tidak punya email, dilewati.",
                    self.id,
                    user.name,
                    user.id,
                )
        _logger.info(
            "[task_deadline_reminder] Task id=%s: ringkasan email — %s penerima terkirim.",
            self.id,
            sent,
        )

    @api.model
    def _test_send_deadline_reminder(self, test_email):
        """Kirim satu email uji ke alamat tertentu (wizard Settings)."""
        if not test_email:
            raise UserError('Alamat email uji kosong.')
        template = self.env.ref(
            'task_deadline_reminder.email_template_task_deadline_reminder',
            raise_if_not_found=False,
        )
        if not template:
            raise UserError('Template email Task Deadline Reminder tidak ditemukan.')
        project = self.env['project.project'].search([], limit=1)
        if not project:
            raise UserError('Buat minimal satu project agar pengujian email bisa jalan.')
        dummy = self.create({
            'name': 'TEST: Deadline Reminder',
            'project_id': project.id,
            'date_deadline': fields.Date.today(),
            'reminder_method': 'email',
            'user_ids': [(4, self.env.user.id)],
        })
        try:
            email_from = self.env['ir.config_parameter'].sudo().get_param(
                'task_deadline_reminder.task_reminder_email_from'
            )
            template.send_mail(
                dummy.id,
                force_send=True,
                email_values={'email_to': test_email, 'email_from': email_from},
            )
        finally:
            dummy.unlink()