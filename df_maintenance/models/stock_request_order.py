from odoo import _, api, fields, models


class StockRequestOrderInherit(models.Model):
    _inherit = "stock.request"

    work_order_product_id = fields.Many2one(comodel_name="df.work.order.product",
                                            string="Producto de orden de trabajo",
                                            )


