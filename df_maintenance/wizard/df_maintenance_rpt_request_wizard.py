# -*- coding: utf-8 -*-
import time
from odoo import models, fields, api
from odoo.modules import module
from xlwt import Workbook,Style,easyxf
import os
import base64
from odoo.exceptions import ValidationError

class df_maintenance_rpt_request_wizard(models.TransientModel):
    _inherit = 'nl.cfg.base.reports'
    _name = 'df.maintenance.rpt.request.wizard'


    date_start = fields.Date('Start Date', required=True,default=fields.Date.context_today)
    date_end = fields.Date('End Date', required=True,default=fields.Date.context_today)

    stage_id = fields.Many2one('maintenance.stage', string='Stage', )
    cost_center_allowed = fields.Many2one('account.analytic.account', string='Brigade Cost Center')
    stock_asset_id = fields.Many2one('df.maintenance.physical.location', string='Asset location')
    equipment_id = fields.Many2one('maintenance.equipment', string='Equipment')


    @api.onchange('cost_center_allowed')
    def _onchange_cost_center_allowed(self):
        if self.cost_center_allowed:
            list = []
            stock_asset_ids = self.env['maintenance.request'].search([('cost_center', '=', self.cost_center_allowed.id)])
            if stock_asset_ids:
                for a in stock_asset_ids:
                    list.append(a.stock_asset_id.id)

            return {'domain': {'stock_asset_id': [('id', 'in', list)]}}

    @api.onchange('stock_asset_id')
    def _onchange_stock_asset_id(self):
        if self.stock_asset_id:
            list1 = []
            equipment_ids = self.env['maintenance.request'].search(
                [('cost_center', '=', self.cost_center_allowed.id), ('stock_asset_id', '=', self.stock_asset_id.id)])
            if equipment_ids:
                for a in equipment_ids:
                    list1.append(a.equipment_id.id)
            print('..list1...',list1)
            return {'domain': {'equipment_id': [('id', 'in', list1)]}}


    def print_report(self, context=None):

        data_wizard, ori, out = self.load_report_style()

        domin=[]
        ini = self.date_start
        fin = self.date_end


        if data_wizard['date_start']:
            domin.append(('request_date', '>=', ini))
        if data_wizard['date_end']:
            domin.append(('request_date', '<=', fin))

        if data_wizard['stage_id']:
            domin.append(('stage_id', '=', self.stage_id.id))

        if data_wizard['cost_center_allowed']:
            domin.append(('cost_center', '=', self.cost_center_allowed.id))

        if data_wizard['stock_asset_id']:
            domin.append(('stock_asset_id', '=', self.stock_asset_id.id))

        if data_wizard['equipment_id']:
            domin.append(('equipment_id', '=', self.equipment_id.id))


        print('.domin...',domin)

        docids = [x.id for x in self.env['maintenance.request'].search(domin)]
        if not docids:
            raise ValidationError('OPERACIÓN DENEGADA\r\n\r\nSin datos que mostrar')

        # data_wizard['result'] = docids

        data = {'ids': docids,
                'form': {'data_wizard': data_wizard}
                }

        action = self.call_report_action("df_maintenance.action_print_request", data,
                                         horizontal=ori != 'vp', out=out)
        return action
