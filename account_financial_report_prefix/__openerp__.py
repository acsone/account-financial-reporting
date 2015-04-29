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

{
    'name': 'Account Financial Report by Prefixes',
    'summary': """
Financial report based on account codes prefixes""",
    'author': 'ACSONE SA/NV',
    'website': 'http://www.acsone.eu',
    'category': 'Accounting & Finance',
    'version': '1.0',
    'license': 'AGPL-3',
    'depends': [
        'account',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/account_financial_report_prefix_view.xml',
        'views/account_financial_report_view.xml',
    ],
    'demo': [
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
