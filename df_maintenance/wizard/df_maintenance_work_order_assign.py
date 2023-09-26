# -*- coding: utf-8 -*-
from odoo import models, fields, api


class MaintenanceWorkOrderAssign(models.TransientModel):
    _name = "df.maintenance.work.order.assign"
    _description = "Work Order Assignation Completed"

    def assign_order(self):
        context = dict(self._context or {})
        mod_obj = self.env['ir.model.data']
        # form_res = mod_obj.get_object_reference('df_maintenance', 'df_maintenance_work_order_form_view')
        form_res = mod_obj.check_object_reference('df_maintenance', 'df_maintenance_work_order_form_view')
        form_id = form_res and form_res[1] or False
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'df.maintenance.work.order',
            'res_id': int(context['order_id'][0]),
            'view_id': False,
            'views': [(form_id, 'form')],
            'context': "{}",
            'type': 'ir.actions.act_window',
         }



# Vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
