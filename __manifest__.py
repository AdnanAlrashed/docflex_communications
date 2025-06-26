# -*- coding: utf-8 -*-
{
    'name': "DocFlex Communications",
    'summary': "A comprehensive module for managing communications and ticketing in Odoo",
    'summary': "Short (1 phrase/line) summary of the module's purpose",
    'description': """
            Long description of module's purpose
                """,
    'author': "ADAERP Company",
    'website': "https://www.yourcompany.com",
    'category': 'Uncategorized',
    'module_type':'official',
    'version': '18.0.1.0.0',
    # any module necessary for this one to work correctly
    'depends': ['base','hr','mail',
                'website',
                'helpdesk',
                'documents',
                'utm',
                'rating',
                'web_tour',
                'web_cohort',
                'resource',
                'portal',
                'digest',
                ],

    # always loaded
    'data': [
        'data/data.xml',
        'data/referral_type_data.xml',
        'data/email_templates.xml',
        'security/docflex_security.xml',
        'security/ir_rules.xml',
        'security/ir.model.access.csv',
        # 'views/mine_menu.xml',
        'views/docflex_ticket_views.xml',
        'views/ticket_classification_views.xml',
        'views/ticket_sections_views.xml',
        'views/ticket_status_views.xml',
        'views/ticket_priority_views.xml',
        'views/ticket_type_views.xml',
        'views/ticket_summary_views.xml',
        'views/ticket_tag_views.xml',
        'views/ticket_security_views.xml',
        'views/docflex_ticket_stage_views.xml',
        'views/res_partner_views.xml',
        'views/referral_views.xml',
        'views/archive_folder_view.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'assets': {
        'web.assets_backend': [
           
        ],
        'web.qunit_suite_tests': [
        ],
    },
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',

    'installable':True,
    'application':True,
    'license':'LGPL-3',
}

