from odoo import api, fields, models, _, tools
from odoo.osv import expression
from odoo.exceptions import ValidationError


class StockRequestOrder(models.Model):
    _inherit = "stock.request.order"

    order_id = fields.Many2one('df.maintenance.work.order','Order ID')
    employee_id = fields.Many2one('hr.employee', 'Employee')

    def print_vale_work_order(self):
        list = []
        list.append(self.id)
        action_report = self.env.ref('df_maintenance.action_print_receipt').report_action([], data={
            'order_id': self.order_id.id,
            'stock_req_ids': list,
            }, )
        return action_report

