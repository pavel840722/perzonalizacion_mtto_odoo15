# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ReportPrintReceipt(models.AbstractModel):
    _name = 'report.df_maintenance.report_print_maintenance_time_brigade'
    _description = 'Maintenance time for brigade'

    def get_team(self, ids):
        domain_base = [('id', 'in', ids)]
        result = list(set([x.maintenance_team_id for x in self.env['df.maintenance.work.order'].search(domain_base)]))
        return result

    def get_brigada(self, ids, team_id):
        domain_base = [('id', 'in', ids), ('maintenance_team_id', '=', team_id)]
        result = list(set([x.brigade_id for x in self.env['df.maintenance.work.order'].search(domain_base)]))
        return result

    def get_actividad(self, ids, team_id, brigade_id):
        domain_base = [('order_id', 'in', ids), ('order_id.maintenance_team_id', '=', team_id),
                       ('order_id.brigade_id', '=', brigade_id)]
        result = list(set([x.activity_id for x in self.env['df.work.order.employee'].search(domain_base,order='order_id')]))
        return result

    def get_employee(self, ids, team_id, brigade_id, actividad_id):
        domain_base = [('order_id', 'in', ids), ('order_id.maintenance_team_id', '=', team_id),
                       ('order_id.brigade_id', '=', brigade_id),('activity_id', '=', actividad_id)]
        return self.env['df.work.order.employee'].search(domain_base)

    @api.model
    def _get_report_values(self, docids, data=None):
        def get_logo():
            return self.env['nl.cfg.base.reports'].sudo().get_logo(data_form)

        if not data or not data.get('form', False):
            data = {'form': {}}

        docids = [x for x in self.env['df.maintenance.work.order'].search([('id', 'in', data['ids'])])]

        data_form = data['form'].get('data_wizard', {})
        print('Docids que van al rporte' + str(docids))
        reports_functions = self.env['nl.reports.functions']

        data_form.update({
            'logo': get_logo(),
            'docs': docids,
            'user_func': reports_functions,
            'domain_base': data['ids'],
            'get_team': self.get_team,
            'get_brigada': self.get_brigada,
            'get_actividad': self.get_actividad,
            'get_employee': self.get_employee,

        }
        )
        return data_form
