# -*- coding: utf-8 -*-
##############################################################################
#
# This file is part of account_financial_report_prefix,
# an Odoo module.
#
# Authors: ACSONE SA/NV (<http://acsone.eu>)
#
# account_financial_report_prefix is free software:
# you can redistribute it and/or modify it under the terms of the GNU
# Affero General Public License as published by the Free Software
# Foundation,either version 3 of the License, or (at your option) any
# later version.
#
# account_financial_report_prefix is distributed
# in the hope that it will be useful, but WITHOUT ANY WARRANTY; without
# even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
# PURPOSE. See the GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with account_financial_report_prefix.
# If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, fields


class AccountFinancialReportPrefix(models.Model):

    _name = 'account.financial.report.prefix'
    _description = 'Account Financial Report Code Prefix'
    _rec_name = 'name'
    _order = 'name'

    name = fields.Char(string='Account Code Prefix', required='True')

    _sql_constraints = [
        ('prefix_name_unique', 'unique (name)',
         'The Account Code Prefix must be unique !')]


class AccountFinancialReport(models.Model):

    _inherit = 'account.financial.report'

    type = fields.Selection(
        selection_add=[('account_prefix', 'Account Code Prefix'), ])

    account_prefix_ids = fields.Many2many(
        'account.financial.report.prefix',
        'account_account_financial_report_prefix',
        'report_id', 'prefix_id', string='Prefixes',
        help='Set of account codes prefixes '
             'on which the financial report is based')
