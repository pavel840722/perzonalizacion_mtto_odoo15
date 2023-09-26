from odoo import api, Command, fields, models, _
from odoo.osv import expression
from odoo.tools import float_compare, float_round, float_is_zero, OrderedSet


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    total_price = fields.Float('Total Price', compute='_compute_total_price')

    @api.depends('product_uom_qty', 'product_id.standard_price')
    def _compute_total_price(self):
        for record in self:
            if record.product_uom_qty and record.product_id:
                record.total_price = record.product_uom_qty * record.product_id.standard_price

# class StockPicking(models.Model):
#     _inherit = 'stock.picking'
#
#     def button_validate(self):
#         res = super(StockPicking, self).button_validate()
#         requests_order = self.env['stock.request.order'].search([('name','=',self.origin)])
#         for record in requests_order.stock_request_ids:
#             reserved = record.qty_done
#             record.work_order_product_id.product_qty_deliveed = record.work_order_product_id.product_qty_deliveed + reserved
#             record.work_order_product_id.stock_request_order_id = False
#         return res

