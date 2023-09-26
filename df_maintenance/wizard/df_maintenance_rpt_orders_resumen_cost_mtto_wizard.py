# -*- coding: utf-8 -*-
import time
from odoo import models, fields, api
from odoo.modules import module
from xlwt import Workbook, Style, easyxf
import os
import base64
from odoo.exceptions import ValidationError


class df_maintenance_rpt_orders_resumen_cost_mtto_wizard(models.TransientModel):
    _inherit = 'nl.cfg.base.reports'
    _name = 'df.maintenance.rpt.orders.resumen.cost.mtto.wizard'

    date_start = fields.Date('Start Date', required=True, default=fields.Date.context_today)
    date_end = fields.Date('End Date', required=True, default=fields.Date.context_today)

    cost_center = fields.Many2one('account.analytic.account', string='Cost Center',
                                  domain="[('group_id', '=', False)]")

    def print_report(self, context=None):

        data_wizard, ori, out = self.load_report_style()

        domin = [('order_no', '!=', 'Nuevo')]
        ini = self.date_start
        fin = self.date_end

        if data_wizard['date_start']:
            domin.append(('create_date', '>=', ini))

        if data_wizard['date_end']:
            domin.append(('create_date', '<=', fin))

        if data_wizard['cost_center']:
            # domin.append(('cc_asset_id', '=', self.cost_center.id))
            domin.append(('asset_id.cost_center.code', '=', self.cost_center.code))

        print ('Domi.....', domin)
        docids = [x.id for x in self.env['df.maintenance.work.order'].search(domin, order='brigade_cost_center')]

        if not docids:
            raise ValidationError('OPERACIÓN DENEGADA\r\n\r\nSin datos que mostrar')

        data = {'ids': docids,
                'form': {'data_wizard': data_wizard}
                }

        action = self.call_report_action("df_maintenance.action_print_orders_resumen_cost_mtto", data,
                                         horizontal=ori != 'vp', out=out)
        return action
