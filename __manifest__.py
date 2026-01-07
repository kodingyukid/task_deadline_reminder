{
    'name': 'Task Deadline Reminder',
    'version': '17.0.3.0.0',
    'summary': 'Send email notifications for tasks with upcoming deadlines.',
    'author': 'KodingYuk',
    'website': 'https://kodingyuk.id',
    'category': 'Project',
    'depends': ['project', 'mail', 'hr'],
    'data': [
        'security/ir.model.access.csv',
        'data/cron.xml',
        'data/mail_template.xml',
        'views/task_reminder_tester_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
