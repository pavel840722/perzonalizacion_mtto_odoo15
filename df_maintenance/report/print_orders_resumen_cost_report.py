# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ReportPrintReceipt(models.AbstractModel):
    _name = 'report.df_maintenance.report_print_orders_resumen_cost'
    _description = 'Print Orders Resumen Coste'

    def get_centro_costo(self, ids):
        domain_base = [('id', 'in', ids)]
        result = list(set([x.asset_id.cost_center for x in self.env['df.maintenance.work.order'].search(domain_base)]))
        return result

    def get_equipos(self, ids, centro_costo_id):
        domain_base = [('id', 'in', ids), ('cc_asset_id', '=', centro_costo_id)]
        result = list(set([x.asset_id for x in self.env['df.maintenance.work.order'].search(domain_base)]))
        return result

    def get_equipos_res(self, ids, centro_costo_id):
        domain_base = [('id', 'in', ids), ('cc_asset_id', '=', centro_costo_id)]
        x = self.env['df.maintenance.work.order'].search(domain_base)
        return x

    def get_ordenes_equipos(self, ids, centro_costo_id, equipo_id):
        domain_base = [('id', 'in', ids), ('cc_asset_id', '=', centro_costo_id), ('asset_id', '=', equipo_id)]
        print('domin.......ordenes' + str(domain_base))
        y = self.env['df.maintenance.work.order'].search(domain_base)
        return [x for x in y if len(x.product_ids) > 0 or len(x.employee_ids)]

    @api.model
    def _get_report_values(self, docids, data=None):
        def get_logo():
            return self.env['nl.cfg.base.reports'].sudo().get_logo(data_form)

        if not data or not data.get('form', False):
            data = {'form': {}}

        docids = [x for x in self.env['df.maintenance.work.order'].search([('id', 'in', data['ids'])])]

        data_form = data['form'].get('data_wizard', {})
        print('Docids' + str(docids))
        reports_functions = self.env['nl.reports.functions']

        data_form.update({
            'logo': get_logo(),
            'docs': docids,
            'user_func': reports_functions,
            'domain_base': data['ids'],
            'get_centro_costo': self.get_centro_costo,
            'get_equipos': self.get_equipos,
            'get_equipos_res': self.get_equipos_res,
            'get_ordenes_equipos': self.get_ordenes_equipos

        }
        )

        return data_form
