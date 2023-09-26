from odoo import models, fields, api, _
from datetime import datetime

class TransferBetweenOrders(models.TransientModel):
    _name = 'df.transfer.between.orders'
    _description = "Transfer Between Orders"

    order_transfer_id = fields.Many2one('df.maintenance.work.order', 'Work order transfer', required=True)
    order_transfer_team_id = fields.Integer(related='order_transfer_id.maintenance_team_id.id')
    order_receive_id = fields.Many2one('df.maintenance.work.order', 'Work order receive', required=True)
    product_ids = fields.Many2many('df.work.order.product', 'mm_transfer_between_orders', 'transfer_id', 'order_transfer_id')

    @api.onchange('order_transfer_id')
    def _onchange_order_transfer_id(self):
        self.order_receive_id = ''


    def transfer_between_orders(self):
        account_move_obj = self.env['account.move']
        account_move_line_obj = self.env['account.move.line']
        for product_work_order in self.product_ids:
            obj_order_product = self.env['df.work.order.product'].create({
                                       'product_id': product_work_order.product_id.id,
                                       'product_qty': product_work_order.product_qty,
                                       'product_uom': product_work_order.product_uom.id,
                                       'price_unit': product_work_order.price_unit,
                                       'amount': product_work_order.amount,
                                       'is_order': product_work_order.is_order,
                                       #'location': product_work_order.location.id,
                                       'store_id': product_work_order.store_id.id,
                                       'date': product_work_order.date,
                                       'delivery_status': product_work_order.delivery_status,
                                       'order_id': self.order_receive_id.id
            })

            stock_request_id = self.env['stock.request'].search([('work_order_product_id','=',product_work_order.id)])
            account_move_objs = self.env['account.move'].browse(stock_request_id.move_ids.ids)
            account_move_objs = stock_request_id.move_ids.account_move_ids
            for account_move in account_move_objs:
                lines = list()

                debito = {'name': account_move.line_ids[1].name, 'account_id': account_move.line_ids[1].account_id.id,'analytic_account_id':account_move.line_ids[1].analytic_account_id.id,
                                                     'credit':account_move.line_ids[1].debit }
                credito = {'name': account_move.line_ids[1].name, 'account_id': account_move.line_ids[1].account_id.id,
                          'analytic_account_id': product_work_order.order_id.request_id.cost_center.id,
                          'debit': account_move.line_ids[1].debit}
                lines.append((0,0,debito))
                lines.append((0,0,credito))

                obj_account_move = account_move_obj.create({
                    # 'name':account_move.name,
                    'journal_id': account_move.journal_id.id,
                    'ref': account_move.ref,
                    'date': account_move.date,
                    'line_ids': lines,
                })
                obj_account_move.write({'state': 'posted'})


            product_work_order.unlink()
        if self.env.context['lang'] == 'es_ES':
            message_id = self.env['df.message.wizard'].create({'message': 'La transferencia fue completada.'})
        else:
            message_id = self.env['df.message.wizard'].create({'message': 'The transfer was completed.'})
        return {
            'name': _('Message'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'df.message.wizard',
            'res_id': message_id.id,
            'target': 'new'
        }
