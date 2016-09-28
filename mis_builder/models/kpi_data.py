# -*- coding: utf-8 -*-
# © 2016 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from openerp import api, fields, models, _


class AbstractKpiDataFactory(models.AbstractModel):

    def _get_basic_domain(self, report_id, date_from, date_to):
        """ return a domain over AbstractKpiData
            that match the given report and overlap
            the given period
        """
        return [
            ('date_from', '<=', date_to),
            ('date_to', '>=', date_from),
            ('report_id', '=', report_id),
        ]

    def _get_model_from_dataset(self, data_set):
        return

    @api.model
    def _search_kpi_data(self, report_id, data_set, date_from, date_to):
        pass


class AbstractKpiData(models.AbstractModel):

    kpi_id = fields.Many2one(
        comodel_name='mis.report.kpi',
        string='KPI',
        required=True)
    report_id = fields.Many2one(
        comodel_name='mis.report',
        related='kpi_id.report_id',
        store=True)
    date_from = fields.Date(
        required=True)
    date_to = fields.Date(
        required=True)
    value = fields.Float(
        required=True)

    _order = 'report_id, kpi_id, date_from'


class MisReportKpiData(AbstractKpiData):

    pass
