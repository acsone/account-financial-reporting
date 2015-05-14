# -*- encoding: utf-8 -*-
##############################################################################
#
#    mis_builder module for Odoo, Management Information System Builder
#    Copyright (C) 2014-2015 ACSONE SA/NV (<http://acsone.eu>)
#
#    This file is a part of mis_builder
#
#    mis_builder is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License v3 or later
#    as published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    mis_builder is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License v3 or later for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    v3 or later along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import logging

from openerp import api, models
from openerp.addons.web.http import Controller, route, request

_logger = logging.getLogger(__name__)


class ExcelExporter(Controller):

    @route('/mis_builder/export/xls/<doc_ids>', type='http', auth='user')
    def excel_export(self, doc_ids):
        doc_ids = [int(doc_ids)]
        docs = request.env['mis.report.instance'].browse(doc_ids)
        docs_computed = {}
        for doc in docs:
            docs_computed[doc.id] = doc.compute()[0]
        docargs = {
            'doc_ids': doc_ids,
            'doc_model': 'mis.report.instance',
            'docs': docs,
            'docs_computed': docs_computed,
        }
        html = request.env['report'].\
            render('mis_builder.report_mis_report_instance_xls', docargs)
        return request.make_response(html, headers=[
            ('Content-Type', 'text/html'),
            ('Content-Disposition', 'attachment; filename=mis_report.xls;')
        ])
