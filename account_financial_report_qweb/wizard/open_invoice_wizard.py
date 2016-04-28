# -*- coding: utf-8 -*-
# Author: Andrea andrea4ever Gallina
# Author: Francesco OpenCode Apruzzese
# Author: Ciro CiroBoxHub Urselli
# Copyright 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields, api, _
from openerp.exceptions import Warning as UserError
from datetime import datetime


class OpenInvoiceWizard(models.TransientModel):

    _name = 'open.invoice.wizard'

    company_id = fields.Many2one(
        'res.company', required=True,
        default=lambda s: s.env.user.company_id)
    at_date = fields.Date(
        required=True,
        default=fields.Date.to_string(datetime.today()))
    partner_ids = fields.Many2many(
        'res.partner', string='Filter partners')
    amount_currency = fields.Boolean(
        "With Currency", help="It adds the currency column")
    group_by_currency = fields.Boolean(
        "Group Partner by currency", help="It adds the currency column")
    result_selection = fields.Selection([
        ('customer', 'Receivable Accounts'),
        ('supplier', 'Payable Accounts'),
        ('customer_supplier', 'Receivable and Payable Accounts')],
        "Partner's", required=True, default='customer')
    target_move = fields.Selection([
        ('posted', 'All Posted Entries'),
        ('all', 'All Entries')], 'Target Moves',
        required=True, default='all')
    until_date = fields.Date(
        "Clearance date",
        help="""The clearance date is essentially a tool used for debtors
        provisionning calculation.
        By default, this date is equal to the the end date (
        ie: 31/12/2011 if you select fy 2011).
        By amending the clearance date, you will be, for instance,
        able to answer the question : 'based on my last
        year end debtors open invoices, which invoices are still
        unpaid today (today is my clearance date)?'""")

    @api.onchange('at_date')
    def onchange_atdate(self):
        self.until_date = self.at_date

    @api.onchange('until_date')
    def onchange_untildate(self):
        # ---- until_date must be always >= of at_date
        if self.until_date:
            if self.until_date < self.at_date:
                raise UserError(
                    'Until Date must be equal or greater than At Date')

    @staticmethod
    def _get_domain(data):
        account_type = ('payable', 'receivable')
        if data['result_selection'] == 'customer':
            account_type = ('receivable', )
        elif data['result_selection'] == 'supplier':
            account_type = ('payable', )
        domain = [
            ('company_id', '=', data['company_id'].id),
            ('move_id.date', '<=', data['at_date']),
            ('account_id.user_type_id.type', 'in', account_type)
            ]
        if data['target_move'] != 'all':
            domain.append(('move_id.state', 'in', ('posted', )), )
        if data['partner_ids']:
            domain.append(('partner_id', 'in', [p.id
                                                for p
                                                in data['partner_ids']]), )
        return domain

    @staticmethod
    def _get_move_line_data(move):
        label = move.name
        if move.invoice_id:
            label = '{label} ({inv_nummber})'.format(
                label=label, inv_nummber=move.invoice_id.number)
        return {
            'date': move.date,
            'entry': move.move_id.name,
            'journal': move.move_id.journal_id.code,
            'reference': move.ref,
            'label': label,
            'rec': move.full_reconcile_id.name,
            'due_date': move.date_maturity,
            'debit': move.debit,
            'credit': move.credit,
            }

    @api.multi
    def print_report(self):
        self.ensure_one()
        moves = self.env['account.move.line'].search(
            self._get_domain(self), order='date asc')
        if not moves:
            return True  # ----- Show a message here
        datas = {}
        for move in moves:
            account = '{code} - {name}'.format(
                code=move.account_id.code,
                name=move.account_id.name)
            partner = move.partner_id.name
            if account not in datas:
                datas[account] = {}
            if partner not in datas[account]:
                datas[account][partner] = []
            datas[account][partner].append(
                self._get_move_line_data(move))
        generals = {
            'company': self.company_id.name,
            'fiscal_year': '',
            'at_date': self.at_date,
            'account_filters': dict(
                self._columns['result_selection'].selection)[
                self.result_selection],
            'target_moves': dict(
                self._columns['target_move'].selection)[self.target_move],
            }
        return self.env['report'].get_action(
            self, 'account_financial_report_qweb.open_invoice_report_qweb',
            data={'data': datas, 'general': generals})