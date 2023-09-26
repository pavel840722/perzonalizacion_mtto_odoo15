# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    order_id = fields.Many2one('df.maintenance.work.order', related='move_lines.work_order_product_id.order_id',
        string="Purchase Orders", readonly=True)


class StockMove(models.Model):
    _inherit = 'stock.move'

    work_order_product_id = fields.Many2one('df.work.order.product',
        'Work Order Product', ondelete='set null', index=True, readonly=True)
    created_work_order_product_id = fields.Many2one('df.work.order.product',
        'Created Work Order Product', ondelete='set null', readonly=True, copy=False)

    @api.model
    def _prepare_merge_moves_distinct_fields(self):
        distinct_fields = super(StockMove, self)._prepare_merge_moves_distinct_fields()
        distinct_fields += ['work_order_product_id', 'created_work_order_product_id']
        return distinct_fields

    @api.model
    def _prepare_merge_move_sort_method(self, move):
        move.ensure_one()
        keys_sorted = super(StockMove, self)._prepare_merge_move_sort_method(move)
        keys_sorted += [move.work_order_product_id.id, move.work_order_product_id.id]
        return keys_sorted

class StockPicking(models.Model):
    _inherit = 'stock.location'

    analytic_account = fields.Many2one('account.analytic.account', 'Analytic Account')


