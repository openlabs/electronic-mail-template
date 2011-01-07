# -*- coding: UTF-8 -*-
# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
"Email Template"
from __future__ import with_statement

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO
import mimetypes
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.utils import formatdate

from genshi.template import TextTemplate
from trytond.model import ModelView, ModelSQL, fields
from trytond.tools import safe_eval, get_smtp_server
from trytond.transaction import Transaction
from trytond.pyson import Eval


def split_emails(email_ids):
    """Email IDs could be separated by ';' or ','

    >>> email_list = '1@x.com;2@y.com , 3@z.com '
    >>> emails = split_emails(email_list)
    >>> emails
    ['1@x.com', '2@y.com', '3@z.com']

    :param email_ids: email id
    :type email_ids: str or unicode
    """
    if not email_ids:
        return [ ]
    email_ids = email_ids.replace(' ', '').replace(',', ';')
    return email_ids.split(';')


def recepients_from_fields(email_record):
    """
    Returns a list of email addresses who are the recipients of this email

    :param email_record: Browse record of the email
    """
    recepients = [ ]
    for field in ('to', 'cc', 'bcc'):
        recepients.extend(split_emails(getattr(email_record, field)))
    return recepients


class Template(ModelSQL, ModelView):
    'Email Template'
    _name = 'electronic_mail.template'
    _description = __doc__
    _inherits = {
        'electronic_mail': 'electronic_mail',
        }

    #: The design inherits from elecronic mail because a template
    #: is infact the source record to generate an electronic mail
    electronic_mail = fields.Many2One(
        'electronic_mail', 'Email', required=True, ondelete='CASCADE')
    model = fields.Many2One(
        'ir.model', 'Model', required=True)

    # All the following fields are expression fields which are evaluated
    # safely, the other fields are directly used from electronic_mail itself
    language = fields.Char(
        'Language', help='Expression to find the ISO langauge code')
    plain = fields.Text('Plain Text Body')
    html = fields.Text('HTML Body')
    reports = fields.Many2Many(
        'electronic_mail.template-ir.action.report',
        'template', 'report', 'Reports')
    engine = fields.Selection(
        'get_engines', 'Engine', required=True)
    triggers = fields.One2Many(
        'ir.trigger', 'email_template', 'Triggers',
        context={
            'model': Eval('model'),
            'email_template': True,
            })

    def default_engine(self):
        '''Default Engine'''
        return 'genshi'

    def get_engines(self):
        '''Returns the engines as list of tuple

        :return: List of tuples
        '''
        engines = [ 
            ('python', 'Python'),
            ('genshi', 'Genshi'),
        ]
        return engines

    def eval(self, template, expression, record):
        '''Evaluates the given :attr:expression

        :param template: Browse record of the template
        :param expression: Expression to evaluate
        :param record: The browse record of the record
        '''
        engine_method = getattr(self, '_engine_' + template.engine)
        return engine_method(expression, record)

    def template_context(self, record):
        """Generate the tempalte context

        This is mainly to assist in the inheritance pattern
        """
        return {'record': record}

    def _engine_python(self, expression, record):
        '''Evaluate the pythonic expression and return its value
        '''
        if expression is None:
            return u''

        assert record is not None, 'Record is undefined'
        template_context = self.template_context(record)
        return safe_eval(expression, template_context)

    def _engine_genshi(self, expression, record):
        '''
        :param expression: Expression to evaluate
        :param record: Browse record
        '''
        if not expression:
            return u''

        template = TextTemplate(expression)
        template_context = self.template_context(record)
        return template.generate(**template_context).render(encoding='UTF-8')

    def render(self, template, record):
        '''Renders the template and returns as email object
        :param template: Browse Record of the template
        :param record: Browse Record of the record on which the template
            is to generate the data on
        :return: 'email.message.Message' instance
        '''

        message = MIMEMultipart('alternative')
        message['date'] = formatdate()

        language = Transaction().context.get('language', 'en_US')
        if template.language:
            language = self.eval(template, template.language, record)

        with Transaction().set_context(langauge = language):
            template = self.browse(template.id)

            # Simple rendering fields
            simple_fields = {
                'from_': 'from',
                'sender': 'sender',
                'to': 'to',
                'cc': 'cc',
                'bcc': 'bcc',
                'subject': 'subject',
                'message_id': 'message-id',
                'in_reply_to': 'in-reply-to',
                }
            for field_name in simple_fields.keys():
                field_expression = getattr(template, field_name)
                eval_result = self.eval(template, field_expression, record)
                if eval_result:
                    message[simple_fields[field_name]] = eval_result

            # Attach reports
            if template.reports:
                reports = self.render_reports(
                    template, record
                    )
                for report in reports:
                    data, filename = report[1:3]
                    content_type, _ = mimetypes.guess_type(filename)
                    maintype, subtype = (
                        content_type or 'application/octet-stream'
                        ).split('/', 1)

                    attachment = MIMEBase(maintype, subtype)
                    attachment.set_payload(data)

                    attachment.add_header(
                        'Content-Disposition', 'attachment', filename=filename)
                    attachment.add_header(
                        'Content-Transfer-Encoding', 'base64')
                    message.attach(attachment)

            # HTML & Text Alternate parts
            plain = self.eval(template, template.plain, record)
            html = self.eval(template, template.html, record)
            message.attach(MIMEText(plain, 'plain'))
            message.attach(MIMEText(html, 'html'))

            # Add headers
            for header in template.headers:
                message.add_header(
                    header.name,
                    unicode(self.eval(template, header.value, record))
                )

        return message

    def render_reports(self, template, record):
        '''Renders the reports and returns as a list of tuple

        :param template: Browse Record of the template
        :param record: Browse Record of the record on which the template
            is to generate the data on
        :return: List of tuples with:
            report_type
            data
            the report name
        '''
        reports = [ ]
        for report_action in template.reports:
            report = self.pool.get(report_action.report_name, type='report')
            reports.append(report.execute([record.id], {'id': record.id}))

        # The boolean for direct print in the tuple is useless for emails
        return [(r[0], r[1], r[3]) for r in reports]

    def render_and_send(self, template_id, record_ids):
        """
        Render the template identified by template_id for
        the records identified from record_ids
        """
        template = self.browse(template_id)
        record_object = self.pool.get(template.model.model)
        email_object = self.pool.get('electronic_mail')

        for record in record_object.browse(record_ids):
            email_message = self.render(template, record)
            email_id = email_object.create_from_email(
                email_message, template.mailbox.id)
            self.send_email(email_id)
        return True

    def mail_from_trigger(self, record_ids, trigger_id):
        """
        To be used with ir.trigger to send mails automatically

        The process involves identifying the tempalte which needs
        to be pulled when the trigger is.

        :param record_ids: IDs of the records
        :param trigger_id: ID of the trigger
        """
        trigger_obj = self.pool.get('ir.trigger')
        trigger = trigger_obj.browse(trigger_id)
        return self.render_and_send(trigger.email_template.id, record_ids)

    def send_email(self, email_id):
        """
        Send out the given email using the SMTP_CLIENT if configured in the
        Tryton Server configuration

        :param email_id: ID of the email to be sent
        """
        email_obj = self.pool.get('electronic_mail')

        email_record = email_obj.browse(email_id)
        recepients = recepients_from_fields(email_record)

        server = get_smtp_server()
        server.sendmail(email_record.from_, recepients,
            email_obj._get_email(email_record))
        server.quit()
        return True

Template()


class TemplateReport(ModelSQL):
    'Template - Report Action'
    _name = 'electronic_mail.template-ir.action.report'
    _description = __doc__

    template = fields.Many2One('electronic_mail.template', 'Template')
    report = fields.Many2One('ir.action.report', 'Report')

TemplateReport()
