# -*- coding: utf-8 -*-
import time
from odoo import models, fields, api
from odoo.modules import module
from xlwt import Workbook,Style,easyxf
import os
import base64
from odoo.exceptions import ValidationError

class df_maintenance_rpt_maintenance_time_wizard(models.TransientModel):
    _inherit = 'nl.cfg.base.reports'
    _name = 'df.maintenance.rpt.maintenance.time.wizard'

    date_start = fields.Date('Start Date', required=True, default=fields.Date.context_today)
    date_end = fields.Date('End Date', required=True, default=fields.Date.context_today)

    maintenance_team_id = fields.Many2one('maintenance.team', string='Maintenance area')

    def print_report(self, context=None):

        data_wizard, ori, out = self.load_report_style()

        domin=[]
        ini = self.date_start
        fin = self.date_end

        if data_wizard['date_start']:
            domin.append(('create_date', '>=', ini))
        if data_wizard['date_end']:
            domin.append(('create_date', '<=', fin))

        if data_wizard['maintenance_team_id']:
            domin.append(('maintenance_team_id', '=', self.maintenance_team_id.id))


        docids = [x.id for x in self.env['df.maintenance.work.order'].search(domin)]
        if not docids:
            raise ValidationError('OPERACIÓN DENEGADA\r\n\r\nSin datos que mostrar')

        #data_wizard['result'] = docids

        data = {'ids': docids,
                'form': {'data_wizard': data_wizard}
                }

        action = self.call_report_action("df_maintenance.action_print_maintenance_time", data,
                                         horizontal=ori != 'vp', out=out)
        return action
