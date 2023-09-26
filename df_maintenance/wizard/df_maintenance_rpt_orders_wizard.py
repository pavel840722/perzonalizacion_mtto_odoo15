# -*- coding: utf-8 -*-
import time
from odoo import models, fields, api
from odoo.modules import module
from xlwt import Workbook, Style, easyxf
import os
import base64
from odoo.exceptions import ValidationError


class df_maintenance_rpt_orders_wizard(models.TransientModel):
    _inherit = 'nl.cfg.base.reports'
    _name = 'df.maintenance.rpt.orders.wizard'

    date_start = fields.Date('Start Date', required=True, default=fields.Date.context_today)
    date_end = fields.Date('End Date', required=True, default=fields.Date.context_today)
    state = fields.Selection([('free', 'Free'),
                              ('in_progress', 'In progress'),
                              ('finished', 'Finished'),
                              ('posted', 'Posted'),
                              ('history', 'History'),
                              ('cancelled', 'Cancelled')])

    maintenance_team_id = fields.Many2one('maintenance.team', string='Maintenance area')
    brigade_id = fields.Many2one('df.maintenance.brigade', string='Brigade')
    brigade_cost_center = fields.Many2one('account.analytic.account', string='Brigade Cost Center')

    @api.onchange('maintenance_team_id')
    def _onchange_state_id(self):
        if self.maintenance_team_id:
            ids = [record.analytic_account.id for record in self.maintenance_team_id.brigades]
            return {'domain': {'brigade_cost_center': [('id', 'in', ids)]}}
        else:
            return {'domain': {'brigade_cost_center': []}}

    def print_report(self, context=None):

        data_wizard, ori, out = self.load_report_style()

        domin = []
        ini = self.date_start
        fin = self.date_end
        if data_wizard['state']:
            domin.append(('state', '=', data_wizard['state']))
        if data_wizard['date_start']:
            domin.append(('create_date', '>=', ini))
        if data_wizard['date_end']:
            domin.append(('create_date', '<=', fin))

        if data_wizard['maintenance_team_id']:
            domin.append(('maintenance_team_id', '=', self.maintenance_team_id.id))

        if data_wizard['brigade_id']:
            domin.append(('brigade_id', '=', self.brigade_id.id))

        docids = [x.id for x in self.env['df.maintenance.work.order'].search(domin)]
        if not docids:
            raise ValidationError('OPERACIÓN DENEGADA\r\n\r\nSin datos que mostrar')

        # data_wizard['result'] = docids

        data = {'ids': docids,
                'form': {'data_wizard': data_wizard}
                }

        if self.env.context.get('rpt', 'orden') == 'orden':
            action = self.call_report_action("df_maintenance.action_print_orders", data,
                                             horizontal=ori != 'vp', out=out)
        else:
            action = self.call_report_action("df_maintenance.action_print_maintenance_time_brigade", data,
                                             horizontal=ori != 'vp', out=out)
        return action
