# -*- coding: UTF-8 -*-
# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.

{
    'name': 'Electronic Mail Template',
    'description': '''Electronic mail template''',
    'version': '2.2.0.2',
    'author': 'Openlabs Technologies & Consulting (P) LTD',
    'email': 'info@openlabs.co.in',
    'website': 'http://openlabs.co.in',
    'active': True,
    'depends': [
        'ir',
        'res',
        'electronic_mail',
    ],
    'xml': [
        'template.xml',
        'trigger.xml',
    ],
    'translation': [
    ],
}

