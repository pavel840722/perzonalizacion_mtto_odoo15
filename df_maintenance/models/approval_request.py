# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ApprovalRequestInherit(models.Model):
    _inherit = 'approval.request'

    work_order_id = fields.Many2one('df.maintenance.work.order')
    account_analytic_id = fields.Many2one('account.analytic.account')

class ApprovalProductLine(models.Model):
    _inherit = 'approval.product.line'

    work_order_product_id = fields.Many2one('df.work.order.product','Work Order Product')