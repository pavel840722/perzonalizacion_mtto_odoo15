# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ReportPrintReceipt(models.AbstractModel):
    _name = 'report.df_maintenance.report_print_maintenance_time'
    _description = 'Print Maintenance time'

    @api.model
    def _get_report_values(self, docids, data=None):

        def get_logo():
            return self.env['nl.cfg.base.reports'].sudo().get_logo(data_form)

        if not data or not data.get('form', False):
            data = {'form': {}}

        #order_report = 'brigade_id,maintenance_team_id'
        order_report = 'maintenance_team_id,brigade_id'

        docids = [x for x in self.env['df.maintenance.work.order'].search([('id', 'in', data['ids'])],
                                                                          order=order_report)]

        data_form = data['form'].get('data_wizard', {})

        reports_functions = self.env['nl.reports.functions']
        data_form.update({
            'logo': get_logo(),
            'docs': docids,
            'user_func': reports_functions,
        }
        )

        return data_form



