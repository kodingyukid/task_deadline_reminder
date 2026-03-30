from odoo import fields, models

class TaskReminderTester(models.TransientModel):
    _name = 'task.reminder.tester'
    _description = 'Task Deadline Reminder Tester'

    employee_id = fields.Many2one(
        'hr.employee', 
        string="Employee to Test", 
        required=True,
        help="Select an employee to send the test email to their work email address."
    )

    def action_send_test_email(self):
        self.ensure_one()
        test_email = self.employee_id.work_email
        self.env['project.task']._test_send_deadline_reminder(test_email)
        return {'type': 'ir.actions.act_window_close'}

    def action_send_test_whatsapp(self):
        self.ensure_one()
        if not self.employee_id.mobile_phone:
            raise Exception("Employee tidak memiliki nomor telepon mobile!")
        
        # Create dummy task for testing
        dummy_task = self.env['project.task'].create({
            'name': 'Test Task',
            'project_id': self.env['project.project'].search([], limit=1).id,
            'user_ids': [(4, self.employee_id.user_id.id)] if self.employee_id.user_id else False,
            'date_deadline': fields.Date.today(),
            'reminder_method': 'whatsapp'
        })
        
        try:
            dummy_task._send_whatsapp_reminder()
            dummy_task.unlink()
            return {'type': 'ir.actions.act_window_close'}
        except Exception as e:
            dummy_task.unlink()
            raise e
