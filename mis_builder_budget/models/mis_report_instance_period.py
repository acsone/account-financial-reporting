# -*- coding: utf-8 -*-
# Copyright 2017 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class MisReportInstancePeriod(models.Model):

    _inherit = 'mis.report.instance.period'

    source = fields.Selection(
        selection_add=[
            ('mis_budget', 'MIS Budget'),
        ],
    )
    source_mis_budget = fields.Many2one(
        comodel_name='mis.budget',
        string='Budget',
    )
