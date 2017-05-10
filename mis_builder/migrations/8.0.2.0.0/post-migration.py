# -*- coding: utf-8 -*-
# © 2017 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


def migrate(cr, version):
    cr.execute("""
        INSERT INTO mis_report_kpi_expression
            (create_uid, create_date, write_uid, write_date,
             kpi_id, name, sequence)
        SELECT create_uid, create_date, write_uid, write_date,
               id, old_expression, sequence
        FROM mis_report_kpi
    """)
    cr.execute("""
        ALTER TABLE mis_report_kpi
        DROP COLUMN old_expression
    """)
