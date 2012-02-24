# -*- coding: UTF-8 -*-
# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
"Trigger Extension"

from trytond.model import ModelSQL, ModelView, fields
from trytond.transaction import Transaction
from trytond.pool import Pool


class Trigger(ModelSQL, ModelView):
    "Extend triggers to use Email template"
    _name = 'ir.trigger'

    email_template = fields.Many2One(
        'electronic_mail.template', 'Template', 
        )

    def default_model(self):
        """If invoked from the email_template fill model
        """
        return Transaction().context.get('model', False)

    def default_action_model(self):
        """If invoked from the email_template fill 
        action model as email_template
        """
        model_obj = Pool().get('ir.model')

        email_trigger = Transaction().context.get('email_template', False)
        if not email_trigger:
            return False

        model_ids = model_obj.search(
            [('model', '=', 'electronic_mail.template')])
        assert len(model_ids) == 1, 'Unexpected result for model search'
        return model_ids[0]

    def default_action_function(self):
        """If invoked from the email_template fill
        action function as 'mail_from_trigger'
        """
        email_trigger = Transaction().context.get('email_template', False)
        return email_trigger and 'mail_from_trigger' or False

Trigger()
