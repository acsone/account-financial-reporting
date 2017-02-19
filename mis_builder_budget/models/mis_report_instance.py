# -*- coding: utf-8 -*-
# Copyright 2017 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class MisReportInstance(models.Model):

    _inherit = 'mis.report.instance'

    def _add_column_mis_budget(
            self, aep, kpi_matrix, period, label, description):

        # fetch budget data for the period
        base_domain = [('budget_id', '=', period.source_mis_budget.id)]
        kpi_data = self.env['mis.budget.item']._query_kpi_data(
            period.date_from, period.date_to, base_domain)

        # get relevant subkpis
        if period.subkpi_ids:
            # subkpi filter
            subkpis = [subkpi for subkpi in self.subkpi_ids
                       if subkpi in period.subkpi_ids]
        else:
            subkpis = self.report_id.subkpi_ids

        if subkpis:
            raise RuntimeError("not implemented")
            # TODO
            # subkpi_indexes = dict(enumerate(subkpis))
            # locals_dict = defaultdict(
            #     lambda: ['AccountingNone'] * len(subkpis))
        else:
            locals_dict = {}

        for kpi_expression, amount in kpi_data.items():
            if subkpis:
                raise RuntimeError("not implemented")
            else:
                locals_dict[kpi_expression.kpi_id.name] = amount

        self.report_id.declare_and_compute_period(
            kpi_matrix,
            period.id,
            label,
            description,
            aep,
            period.date_from,
            period.date_to,
            self.target_move,
            period.subkpi_ids,
            get_additional_move_line_filter=None,  # TODO
            get_additional_query_filter=None,
            locals_dict=locals_dict)

    def _add_column(self, aep, kpi_matrix, period, label, description):
        if period.source == 'mis_budget':
            return self._add_column_mis_budget(
                aep, kpi_matrix, period, label, description)
        else:
            return super(MisReportInstance, self)._add_column(
                aep, kpi_matrix, period, label, description)
