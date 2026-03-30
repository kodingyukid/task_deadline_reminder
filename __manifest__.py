{
    'name': 'Task Deadline Reminder',
    'version': '1.0',
    'category': 'Project Management',
    'summary': 'Send deadline reminders for tasks via email and WhatsApp',
    'description': """
Task Deadline Reminder Module
==============================

This module adds functionality to send deadline reminders for tasks:
- Email reminders with customizable templates
- WhatsApp reminders using Evolution API
- Configurable reminder methods (Email, WhatsApp, or Both)
- Test functionality for both email and WhatsApp
- Automated cron job for daily deadline checking

Features:
- Configurable sender email
- Evolution API integration for WhatsApp
- Customizable message templates
- Employee-based reminder testing
- Automatic deadline checking
""",
    'author': 'Your Company',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'project',
        'hr',
        'mail',
    ],
    'data': [
        'data/cron.xml',
        'data/mail_template.xml',
        'security/ir.model.access.csv',
        'views/project_task_views.xml',
        'views/res_config_settings_views.xml',
        'views/task_reminder_tester_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
