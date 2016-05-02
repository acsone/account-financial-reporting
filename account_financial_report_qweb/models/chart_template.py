# -*- coding: utf-8 -*-
# © 2016 Akretion (http://www.akretion.com)
# Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openerp import models, fields, api
from openerp.exceptions import UserError


class AccountChartTemplate(models.Model):
    _inherit = 'account.chart.template'

    trial_balance_report_id = fields.Many2one(
        'mis.report',
        string="Trial Balance Report")
    balance_sheet_report_id = fields.Many2one(
        'mis.report',
        string="Balance Sheet Report")
    profit_and_loss_report_id = fields.Many2one(
        'mis.report',
        string="Profit and Lost Report")

    @api.model
    def get_report_action(self, report_name):
        company = self.env['res.users'].browse(self._uid).company_id
        mis_report = company.chart_template_id['%s_report_id' % report_name]
        if not mis_report:
            raise UserError(
                "Not %s report have been configured on this chart account"
                % report_name)
        return mis_report.get_wizard_report_action()
