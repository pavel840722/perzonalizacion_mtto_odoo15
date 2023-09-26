from odoo import models, fields, api,_
from odoo.exceptions import ValidationError

# class MaintenanceProductCheckExists(models.TransientModel):
#     _name = 'df.maintenance.product.check.exists'
#
#     # work_order_id = fields.Many2one('df.maintenance.work.order', 'Orden de trabajo')
#     product_exist_id = fields.Many2one('df.work.order.product', 'Product',)
#     existence = fields.One2many('df.maintenance.product.check.exists.extra','product_check_id',String="Location",readonly=True)
#     dont_existence = fields.Boolean('Dont Existence', default=False)
#
#     @api.model
#     def create(self, vals):
#         product_check = vals.get('product_exist_id')
#         product = self.env['df.work.order.product'].search([('id','=',product_check)])
#         product_id = product.product_id.id
#         warehouse_ids = self.env['stock.warehouse'].search([])
#         existence_ids = self.env['stock.quant'].search([('product_id','=',product_id)])
#         list=[]
#         for warehouse in warehouse_ids:
#             cont = 0
#             for existence in existence_ids:
#                 if warehouse.lot_stock_id.id == existence.location_id.id:
#                     cont = cont + existence.available_quantity
#             if cont > 0:
#                 vals_aux = (0, 0, {'warehouse_id': warehouse.id,
#                                    'cant': cont
#                                    })
#                 list.append(vals_aux)
#         vals['existence'] = list
#
#         if len(list) == 0:
#             vals['dont_existence'] = True
#
#         return super(MaintenanceProductCheckExists, self).create(vals)
#
#     def generate_purchase(self):
#         approval = self.env['approval.request']
#         approval_req = approval.create({
#             '__last_update': False,
#             'request_owner_id': self.env.user.id,
#             'category_id': self.env.ref('approvals_purchase.approval_category_data_rfq').id,
#             'account_analytic_id': self.product_exist_id.order_id.brigade_cost_center.id,  # cuenta analitica o centro de costo que solicita la compra
#             'quantity': 0,
#             'reference': self.product_exist_id.order_id.order_no,
#             'amount': 0,
#             'employee_id': False,
#             'contract_id': False,
#             'date': False,
#             'date_start': False,
#             'date_end': False,
#             'location': False,
#             'partner_id': False,
#             'reference': False,
#             # Lineas de productos con sus cantidades  product_line_ids
#             # product_id es una relación con producto, description puede ser la del producto o una especificada
#             # quantity es la cantidad(es un float), product_uom_id el id de la unidad de medida
#             'product_line_ids': [
#                 [0, False, {'product_id': self.product_exist_id.product_id.id,
#                             'description': self.product_exist_id.product_id.name,
#                             'warehouse_id': 1,
#                             'quantity': self.product_exist_id.product_qty,
#                             'product_uom_id': self.product_exist_id.product_uom.id}],
#                 # [0, False,
#                 #  {'product_id': 46113, 'description': '[10100016007] CAMISA DEL EJE', 'warehouse_id': 1, 'quantity': 25,
#                 #   'product_uom_id': 1}]
#             ],
#             'reason': '<p><br></p>',
#             'message_follower_ids': [],
#             'activity_ids': [],
#             'message_ids': []
#         })
#
#         approval_req._onchange_account_analytic()
#
# class MaintenanceProductCheckExistsExtra(models.TransientModel):
#     _name = 'df.maintenance.product.check.exists.extra'
#
#     product_check_id = fields.Many2one('df.maintenance.product.check.exists')
#     warehouse_id = fields.Many2one('stock.warehouse',readonly=True,string="Warehouse")
#     cant = fields.Float('Quanty')
#
#     def agregar(self):
#         if self.product_check_id.product_exist_id.product_qty > self.cant:
#             raise ValidationError(_('There are not enough quanty of products in this location'))
#         else:
#
#
#             self.product_check_id.product_exist_id.write({'location': self.warehouse_id.lot_stock_id})
#             self.product_check_id.product_exist_id.store_id = self.warehouse_id.id



class MaintenanceProductCheckExists(models.TransientModel):
    _name = 'df.maintenance.product.check.exists'

    # work_order_id = fields.Many2one('df.maintenance.work.order', 'Orden de trabajo')
    product_exist_id = fields.Many2one('df.work.order.product', 'Product',)
    existence = fields.One2many('df.maintenance.product.check.exists.extra','product_check_id',String="Location",readonly=True)
    dont_existence = fields.Boolean('Dont Existence', default=False)

    @api.model
    def create(self, vals):
        product_check = vals.get('product_exist_id')
        product = self.env['df.work.order.product'].search([('id','=',product_check)])
        product_id = product.product_id.id
        warehouse_ids = self.env['stock.warehouse'].search([])
        existence_ids = self.env['stock.quant'].search([('product_id','=',product_id)])
        list=[]
        for warehouse in warehouse_ids:
            cont = 0
            for existence in existence_ids:
                if warehouse.lot_stock_id.id == existence.location_id.location_id.id:
                    cont = cont + existence.available_quantity
            if cont > 0:
                vals_aux = (0, 0, {'warehouse_id': warehouse.id,
                                   'cant': cont
                                   })
                list.append(vals_aux)
        vals['existence'] = list

        if len(list) == 0:
            vals['dont_existence'] = True

        return super(MaintenanceProductCheckExists, self).create(vals)

    def generate_purchase(self):
        list = []

        existence_validated = False

        existence = self.env['stock.quant'].search([('product_id', '=', self.product_exist_id.product_id.id),
                                                                ('inventory_quantity', '!=', False)])
        if existence:
            existence_null = [index.available_quantity == 0 for index in existence]
            existence_validated = all(existence_null)
        if len(existence) == 0 or existence_validated:
            request_purchase_incomplete = self.product_exist_id.request_purchase_ids.filtered(lambda r: r.request_status in ('new', 'pending'))
            if not request_purchase_incomplete:
                if self.product_exist_id.product_qty>0:
                        vals_aux = (0, 0, {'product_id': self.product_exist_id.product_id.id,
                            'description': self.product_exist_id.product_id.name,
                            'warehouse_id': 1,
                            'quantity': self.product_exist_id.product_qty,
                            'product_uom_id': self.product_exist_id.product_uom.id,
                            'work_order_product_id': self.product_exist_id.id
                             })
                        list.append(vals_aux)
                else:
                    raise ValidationError(
                        _('Sorry, but can not create a request purchase with 0 quantity'))
            else:
                raise ValidationError(
                                _('Sorry, but this product have a request purchase'))
        else:
            raise ValidationError(
                    _('Sorry, but there are some products that have existence in warehouse'))


        if len(list) > 0:
            approval = self.env['approval.request']
            approval_req = approval.create({
                '__last_update': False,
                'request_owner_id': self.env.user.id,
                'category_id': self.env.ref('approvals_purchase.approval_category_data_rfq').id,
                # No existe ese campo pero si lo hacen es este el codigo q iria
                'account_analytic_id': self.product_exist_id.order_id.request_id.cost_center.id,
                # cuenta analitica o centro de costo que solicita la compra
                'quantity': 0,
                'reference': self.product_exist_id.order_id.order_no,
                'amount': 0,
                'employee_id': False,
                'contract_id': False,
                'date': False,
                'date_start': False,
                'date_end': False,
                'location': False,
                'partner_id': False,
                'reference': False,
                # Lineas de productos con sus cantidades  product_line_ids
                # product_id es una relación con producto, description puede ser la del producto o una especificada
                # quantity es la cantidad(es un float), product_uom_id el id de la unidad de medida
                'product_line_ids': list,
                'reason': '<p><br></p>',
                'message_follower_ids': [],
                'activity_ids': [],
                'message_ids': [],
                'work_order_id': self.product_exist_id.order_id.id
            })
            for record in approval_req.product_line_ids:
                record.work_order_product_id.request_purchase_ids = [(4, approval_req.id)]

            action = self.env["ir.actions.actions"]._for_xml_id(
                "approvals.approval_request_action_to_review_category")
            action['domain'] = [('id', '=', approval_req.id)]
            return action

class MaintenanceProductCheckExistsExtra(models.TransientModel):
    _name = 'df.maintenance.product.check.exists.extra'

    product_check_id = fields.Many2one('df.maintenance.product.check.exists')
    warehouse_id = fields.Many2one('stock.warehouse',readonly=True,string="Warehouse")
    cant = fields.Float('Quanty')

    def agregar(self):
        if self.product_check_id.product_exist_id.product_qty > self.cant:
            raise ValidationError(_('There are not enough quanty of products in this location'))
        else:
            product_id = self.product_check_id.product_exist_id.product_id
            existence_ids = self.env['stock.quant'].search([('product_id', '=', product_id.id)])
            list_allowed = []
            list_realy = []
            cant_req = self.product_check_id.product_exist_id.product_qty
            cant = 0
            for existence in existence_ids:
                if self.warehouse_id.lot_stock_id.id == existence.location_id.location_id.id:
                    list_allowed.append(existence)
            list_allowed = sorted(list_allowed, key=lambda x: x.quantity,reverse=True)
            for location in list_allowed:
                if cant < cant_req:
                    cant = cant + location.quantity
                    list_realy.append(location.location_id.id)

            self.product_check_id.product_exist_id.write({'location': self.warehouse_id.lot_stock_id})
            self.product_check_id.product_exist_id.store_id = self.warehouse_id.id








