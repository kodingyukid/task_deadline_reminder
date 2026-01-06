{
    'name': 'Task Deadline Reminder',
    'version': '17.0.1.0.0',
    'summary': 'Send email notifications for tasks with upcoming deadlines.',
    'author': 'Gemini',
    'website': 'https://www.gemini.com',
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
