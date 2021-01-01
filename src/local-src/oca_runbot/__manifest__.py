# -*- coding: utf-8 -*-
{
    'name': "OCA runbot",
    'summary': "OCA Runbot",
    'description': "OCA Runbot for Odoo 13.0",
    'author': "Alexandre Fayolle, Odoo Community Assoctiation (OCA)",
    'website': "http://runbot.odoo.com",
    'category': 'Website',
    'depends': ['runbot'],
    'data': [
        'templates/dockerfile.xml',
        'data/build_config_data.xml',
        'views/build_config_step_views.xml',
    ],
}
