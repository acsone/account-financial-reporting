# -*- coding: utf-8 -*-
# Copyright 2017 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _


class JournalReportWizard(models.TransientModel):

    _name = 'journal.report.wizard'

    company_id = fields.Many2one(
        comodel_name='res.company',
        default=lambda self: self.env.user.company_id,
        string='Company'
    )
    date_range_id = fields.Many2one(
        comodel_name='date.range',
        string='Date range'
    )
    date_from = fields.Date(
        string="Start date",
        required=True
    )
    date_to = fields.Date(
        string="End date",
        required=True
    )
    journal_ids = fields.Many2many(
        comodel_name='account.journal',
        string="Journals",
        domain="[('company_id', '=', company_id)]",
    )
    move_target = fields.Selection(
        selection='_get_move_targets',
        default='all'
    )

    @api.model
    def _get_move_targets(self):
        return [
            ('all', _("All")),
            ('posted', _("Posted")),
            ('not_posted', _("Not Posted"))
        ]

    @api.onchange('date_range_id')
    def onchange_date_range_id(self):
        self.date_from = self.date_range_id.date_start
        self.date_to = self.date_range_id.date_end

    @api.multi
    def export_as_pdf(self):
        self.ensure_one()
        return self._export()

    @api.multi
    def export_as_xlsx(self):
        self.ensure_one()
        return self._export(xlsx_report=True)

    @api.multi
    def _prepare_report_journal(self):
        self.ensure_one()
        return {
            'date_from': self.date_from,
            'date_to': self.date_to,
            'move_target': self.move_target,
            'company_id': self.company_id.id,
            'journal_ids': [(6, 0, self.journal_ids.ids)]
        }

    @api.multi
    def _export(self, xlsx_report=False):
        self.ensure_one()
        model = self.env['report_journal_qweb']
        report = model.create(self._prepare_report_journal())
        return report.print_report(xlsx_report=xlsx_report)
