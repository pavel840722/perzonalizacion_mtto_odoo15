# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ReportPrintReceipt(models.AbstractModel):
    _name = 'report.df_maintenance.report_print_request'
    _description = 'Print Request'

    @api.model
    def _get_report_values(self, docids, data=None):

        def get_logo():
            return self.env['nl.cfg.base.reports'].sudo().get_logo(data_form)

        if not data or not data.get('form', False):
            data = {'form': {}}

        docids = [x for x in self.env['maintenance.request'].search([('id','in',data['ids'])])]

        data_form = data['form'].get('data_wizard', {})

        reports_functions = self.env['nl.reports.functions']
        data_form.update({
            'logo': get_logo(),
            'docs': docids,
            'user_func': reports_functions,

        }
        )

        print('pepe', data_form)
        return data_form



