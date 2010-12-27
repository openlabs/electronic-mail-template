#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
"Electronic Mail Template test suite"

import sys, os
DIR = os.path.abspath(os.path.normpath(os.path.join(__file__,
    '..', '..', '..', '..', '..', 'trytond')))
if os.path.isdir(DIR):
    sys.path.insert(0, os.path.dirname(DIR))
import unittest

import trytond.tests.test_tryton
from trytond.tests.test_tryton import POOL, DB_NAME, USER, CONTEXT, test_view
from trytond.transaction import Transaction


class TemplateTestCase(unittest.TestCase):
    """Test Electronic mail templates"""

    def setUp(self):
        trytond.tests.test_tryton.install_module('electronic_mail_template')

        self.template_obj = POOL.get('electronic_mail.template')

    def test0010_genshi_test(self):
        "Test Genshi templating with a simple expression"
        expression = u'<h1>Hello ${record["name"]}</h2>'
        record = {'name': 'Cédric'}
        result = self.template_obj._engine_genshi(expression, record)
        self.assertEqual(result, u'<h1>Hello Cédric</h1>')


def suite():
    "Electronic mail Template test suite"
    suite = trytond.tests.test_tryton.suite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(
        TemplateTestCase
        )
    )
    return suite

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())
