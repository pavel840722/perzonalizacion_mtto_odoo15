# -*- coding: utf-8 -*-
import time
from odoo import models, fields, api
from odoo.modules import module
from xlwt import Workbook,Style,easyxf
import os
import base64
from odoo.exceptions import ValidationError

class df_maintenance_rpt_orders_resumen_cost_wizard(models.TransientModel):
    _inherit = 'nl.cfg.base.reports'
    _name = 'df.maintenance.rpt.orders.resumen.cost.wizard'

    def default_cc_ordenes(self):
        centros_cc_ids = self.env['maintenance.request'].search( [])
        result = list(set([x.cost_center for x in self.env['maintenance.request'].search([])]))
        return result

    date_start = fields.Date('Start Date', required=True, default=fields.Date.context_today)
    date_end = fields.Date('End Date', required=True, default=fields.Date.context_today)

    cost_center = fields.Many2one('account.analytic.account', string='Cost Center', default=default_cc_ordenes)
    equipment_id = fields.Many2one('maintenance.equipment', string='Equipment')
    detallado = fields.Boolean('Details',defautl=False)


    @api.onchange('cost_center')
    def _onchange_cost_center(self):
        if self.cost_center:
            equipment_ids = self.env['maintenance.equipment'].search(
                [('cost_center', '=', self.cost_center.id)])

            ids = [record.id for record in equipment_ids]
            return {'domain': {'equipment_id': [('id', 'in', ids)]}}
        else:
            return {'domain': {'equipment_id': []}}


    def print_report(self, context=None):

        data_wizard, ori, out = self.load_report_style()

        domin=[('order_no', '!=', 'Nuevo')]
        ini = self.date_start
        fin = self.date_end

        if data_wizard['date_start']:
            domin.append(('create_date', '>=', ini))

        if data_wizard['date_end']:
            domin.append(('create_date', '<=', fin))

        if data_wizard['cost_center']:
            domin.append(('asset_id.cost_center', '=', self.cost_center.id))


        if data_wizard['equipment_id']:
            domin.append(('asset_id', '=', self.equipment_id.id))



        print('.domin...', domin)

        docids = [x.id for x in self.env['df.maintenance.work.order'].search(domin, order='cc_asset_id_code,asset_id_code')]
        if not docids:
            raise ValidationError('OPERACIÓN DENEGADA\r\n\r\nSin datos que mostrar')

        #data_wizard['result'] = docids

        data = {'ids': docids,
                'form': {'data_wizard': data_wizard}
                }

        action = self.call_report_action("df_maintenance.action_print_orders_resumen_cost", data,
                                         horizontal=ori != 'vp', out=out)
        return action
