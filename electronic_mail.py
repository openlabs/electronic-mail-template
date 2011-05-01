# -*- coding: UTF-8 -*-
# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
"Email"

from email import message_from_string
from collections import defaultdict

from trytond.model import ModelView, ModelSQL, fields


class ElectronicMail(ModelSQL, ModelView):
    "E-Mail module extended to suit inbuilt reading and templating"
    _name = 'electronic_mail'

    body_html = fields.Function(
        fields.Text('HTML (BODY)'), 'get_email_body')
    body_plain = fields.Function(
        fields.Text('Plain Text (BODY)'), 'get_email_body')

    def get_email_body(self, ids, names):
        """Returns the email body
        """
        result = dict.fromkeys(names)
        for name in names:
            result[name] = defaultdict(unicode).fromkeys(ids)

        for email in self.browse(ids):
            message = message_from_string(self._get_email(email))
            for part in message.walk():
                content_type = part.get_content_type()
                for name in names:
                    if content_type == 'text/' + name.lstrip('body_'):
                        result[name][email.id] = part.get_payload()
        return result

    def check_xml_record(self, ids, values):
        '''It should be possible to overwrite templates'''
        return True

ElectronicMail()
