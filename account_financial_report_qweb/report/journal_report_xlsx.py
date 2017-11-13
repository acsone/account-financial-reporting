# -*- coding: utf-8 -*-
# Author: Damien Crier
# Author: Julien Coux
# Copyright 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from . import abstract_report_xlsx
from odoo.report import report_sxw
from odoo import _


class JournalXslx(abstract_report_xlsx.AbstractReportXslx):

    def __init__(
            self, name, table, rml=False, parser=False, header=True,
            store=False):
        super(JournalXslx, self).__init__(
            name, table, rml, parser, header, store)

    def _get_report_name(self):
        return _('Journal')

    def _get_report_columns(self, report):
        return {
            0: {
                'header': _('Entry'),
                'field': 'entry',
                'width': 18
            },
            1: {
                'header': _('Date'),
                'field': 'date',
                'width': 11
            },
            2: {
                'header': _('Account'),
                'field': 'account_code',
                'width': 9
            },
            3: {
                'header': _('Partner'),
                'field': 'partner',
                'width': 25
            },
            4: {
                'header': _('Ref - Label'),
                'field': 'label',
                'width': 40
            },
            5: {
                'header': _('Taxes'),
                'field': 'taxes_description',
                'width': 11
            },
            6: {
                'header': _('Debit'),
                'field': 'debit',
                'type': 'amount',
                'width': 14,
            },
            7: {
                'header': _('Credit'),
                'field': 'credit',
                'type': 'amount',
                'width': 14
            },
        }

    def _get_journal_tax_columns(self, report):
        return {
            0: {
                'header': _('Name'),
                'field': 'tax_name',
                'width': 35
            },
            1: {
                'header': _('Description'),
                'field': 'tax_code',
                'width': 18
            },
            2: {
                'header': _('Base Debit'),
                'field': 'base_debit',
                'type': 'amount',
                'width': 14
            },
            3: {
                'header': _('Base Credit'),
                'field': 'base_credit',
                'type': 'amount',
                'width': 14
            },
            4: {
                'header': _('Base Balance'),
                'field': 'base_balance',
                'type': 'amount',
                'width': 14
            },
            5: {
                'header': _('Tax Debit'),
                'field': 'tax_debit',
                'type': 'amount',
                'width': 14
            },
            6: {
                'header': _('Tax Credit'),
                'field': 'tax_credit',
                'type': 'amount',
                'width': 14
            },
            7: {
                'header': _('Tax Balance'),
                'field': 'tax_balance',
                'type': 'amount',
                'width': 14
            },
        }

    def _get_col_count_filter_name(self):
        return 2

    def _get_col_count_filter_value(self):
        return 3

    def _get_report_filters(self, report):
        label_by_value = {
            value: label
            for value, label in
            self.env['journal.report.wizard']._get_move_targets()
        }

        return [
            [
                _('Company'),
                report.company_id.name
            ],
            [
                _('Date range filter'),
                _('From: %s To: %s') % (report.date_from, report.date_to)
            ],
            [
                _('Target moves filter'),
                _("%s") % label_by_value[report.move_target]
            ],
            [
                _('Journals'),
                ', '.join([
                    "%s - %s" % (report_journal.code, report_journal.name)
                    for report_journal in report.report_journal_ids
                ])

            ]
        ]

    def _generate_report_content(self, workbook, report):
        for report_journal in report.report_journal_ids:
            self._generate_journal_content(workbook, report_journal)

    def _generate_journal_content(self, workbook, report_journal):
        sheet_name = "%s - %s" % (report_journal.code, report_journal.name)
        journal_sheet = self.add_sheet(workbook, sheet_name)
        self.set_sheet(journal_sheet)
        self._set_column_width()

        self.row_pos = 1

        self.write_array_title(sheet_name)
        self.row_pos += 2

        self.write_array_header()
        for move in report_journal.report_move_ids:
            for line in move.report_move_line_ids:
                self.write_line(line)
            self.row_pos += 1

        self._generate_journal_taxes_summary(workbook, report_journal)

    def _generate_journal_taxes_summary(self, workbook, report_journal):
        sheet_name = "Tax - %s - %s" % (
            report_journal.code, report_journal.name)
        tax_journal_sheet = self.add_sheet(workbook, sheet_name)
        self.set_sheet(tax_journal_sheet)

        self.row_pos = 1
        self.write_array_title(sheet_name)
        self.row_pos += 2

        journal_tax_columns = self._get_journal_tax_columns(
            report_journal.report_id)
        self._set_columns_width(journal_tax_columns)

        for col_pos, column in journal_tax_columns.iteritems():
            self.sheet.write(
                self.row_pos, col_pos, column['header'],
                self.format_header_center
            )
        self.row_pos += 1
        for tax_line in report_journal.report_tax_line_ids:
            self._write_line(journal_tax_columns, tax_line)


JournalXslx(
    'report.account_financial_report_qweb.report_journal_xlsx',
    'report_journal_qweb',
    parser=report_sxw.rml_parse
)
