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

from openerp.osv import fields, orm
import openerp.addons.decimal_precision as dp


class AccountFinancialReportOldApi(orm.Model):
    '''
    OLD API style waiting for a complete api migration of
    odoo/account/account_financial_report.py

    An already new style inheritance of account.financial.report model
    is present in models/account_financial_report.py
    '''

    _inherit = 'account.financial.report'

    def _get_balance(self, cr, uid, ids, fields, args, context=None):
        res = super(AccountFinancialReportOldApi, self)._get_balance(
            cr, uid, ids, fields, args, context=context)

        account_obj = self.pool['account.account']

        for report in self.browse(cr, uid, ids, context=context):
            if report.type == 'account_prefix' and report.account_prefix_ids:
                # it's the sum of all accounts whose code starts with one of
                # the given prefixes
                pfxs = [
                    ('code', 'ilike', '%s%%' % x.name)
                    for x in report.account_prefix_ids
                ]
                domain = \
                    [('type', '!=', 'view')] + \
                    eval('[%s]' % ("'|'," * (len(pfxs) - 1))) + \
                    pfxs
                account_ids = account_obj.search(
                    cr, uid, domain, context=context)
                accounts = account_obj.browse(
                    cr, uid, account_ids, context=context)
                for a in accounts:
                    for field in fields:
                        res[report.id][field] += getattr(a, field)
        return res

    # re-evaluate the compute method pointer
    _columns = {
        'balance': fields.function(_get_balance, 'Balance', multi='balance'),
        'debit': fields.function(_get_balance, 'Debit', multi='balance'),
        'credit': fields.function(_get_balance, 'Credit', multi="balance"),
    }
