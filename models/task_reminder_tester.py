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
