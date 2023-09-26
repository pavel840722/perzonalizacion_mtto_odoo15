# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ReportPrintReceipt(models.AbstractModel):
    _name = 'report.df_maintenance.report_print_orders_resumen_cost_mtto'
    _description = 'Resume Cost Maintenance'

    def get_centro_costo(self,ids):
        domain_base = [('id','in',ids)]
        result = list(set([x.asset_id.cost_center for x in self.env['df.maintenance.work.order'].search(domain_base)]))
        return result

    def get_ordenes_cc(self,ids,centro_costo_id):
        domain_base = [('id','in',ids),('asset_id.cost_center','=',centro_costo_id) ]
        return self.env['df.maintenance.work.order'].search(domain_base)

    @api.model
    def _get_report_values(self, docids, data=None):

        def get_logo():
            return self.env['nl.cfg.base.reports'].sudo().get_logo(data_form)

        if not data or not data.get('form', False):
            data = {'form': {}}

        docids = [x for x in self.env['df.maintenance.work.order'].search([('id','in',data['ids'])])]

        data_form = data['form'].get('data_wizard', {})
        print ('Docids que van al rporte' + str(docids))
        reports_functions = self.env['nl.reports.functions']

        data_form.update({
            'logo': get_logo(),
            'docs': docids,
            'user_func': reports_functions,
            'domain_base': data['ids'],
            'get_centro_costo': self.get_centro_costo,
            'get_ordenes_cc': self.get_ordenes_cc,
        }
        )

        return data_form



