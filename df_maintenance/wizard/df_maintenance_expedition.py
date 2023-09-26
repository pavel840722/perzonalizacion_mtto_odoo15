from odoo import models, fields, api,_
from odoo.exceptions import ValidationError
from datetime import datetime

class MaintenanceProductExpedition(models.TransientModel):
    _name = 'df.maintenance.product.expedition'

    warehouse_ids = fields.Many2many(
        "stock.warehouse",
        string="Warehouse",
    )
    product_ids = fields.One2many('df.maintenance.product.expedition.product','expedition_id','Expedition')
    work_order_id = fields.Many2one('df.maintenance.work.order', 'Work Order')

    employee_id = fields.Many2one('hr.employee', 'Employee', domain="[('id', 'in', employee_allowed )]")
    employee_code = fields.Char('Code', related='employee_id.code', readonly=True)
    employee_allowed = fields.Many2many('hr.employee', 'Employee Alloweed', compute='_compute_employee_allowed')

    @api.depends('work_order_id')
    def _compute_employee_allowed(self):
        for record in self:
            list = []
            employee_ids = self.env['hr.employee'].search(
                [('department_id', '=', record.work_order_id.brigade_id.hr_department.id)])
            for employe in employee_ids:
                list.append(employe.id)
            record.employee_allowed = list



    # def create_expedition(self):
    #     expedition = self.env['stock.request.order']
    #     list = []
    #     list_stock =[]
    #     procurement = self.env['procurement.group']
    #     procurement_id = procurement.name_create('OS2023051700020')
    #     for record in self.product_ids:
    #          vals = (0, 0, {
    #                 'product_id': record.product_id.id,
    #                 'product_uom_qty': record.product_uom_qty,
    #                 'product_uom_id': record.product_uom.id,
    #                 'warehouse_id':self.warehouse_id.id,
    #                 'location_id':self.env.ref('stock.stock_location_customers').id,
    #                 'work_order_product_id':record.line_product_id.id,
    #                 'analytic_account_id': self.work_order_id.request_id.cost_center.id,
    #                 'route_id': self.env.ref('stock.route_warehouse0_mto').id,
    #                 'expected_date': datetime.now(),
    #                 'picking_policy': 'one',
    #                 'company_id': self.env.user.company_id.id,
    #                 'procurement_group_id': procurement_id[0],
    #                 'analytic_tag_ids': [[6, False, []]],
    #             })
    #          list.append(vals)
    #     expedition_id = expedition.create({
    #         'order_id':self.work_order_id.id,
    #         'warehouse_id': self.warehouse_id.id,
    #         'location_id': self.env.ref('stock.stock_location_customers').id,
    #         'stock_request_ids': list,
    #         'company_id': self.env.user.company_id.id,
    #         'procurement_group_id': procurement_id[0],
    #         'default_analytic_account_id': self.work_order_id.request_id.cost_center.id,
    #         'picking_policy': 'one',
    #         'expected_date': datetime.now(),
    #         'message_follower_ids': [],
    #                 'activity_ids': [],
    #                 'message_ids': []
    #
    #     })
    #     expedition_id.action_confirm()
    #
    #     for record in self.work_order_id.stock_request_order:
    #        list_stock.append(record.id)
    #     self.work_order_id.write({
    #        'stock_request_order': list_stock
    #     })

    def create_expedition(self):
        stock_req_ids = []
        for warehouse in self.warehouse_ids:
            products_line = self.product_ids.filtered(lambda r: r.warehouse_id == warehouse)

            obj_stock_request_order = self.env['stock.request.order']
            procurement = self.env['procurement.group']
            # OS2023051700001 debes generarlo, te propongo sea No de orden seguido de fecha y hora
            # Ejemplo: Orden 000001 Fecha:17/06/2023 Hora: 00:15 am daría -> 000001202306170015
            date = datetime.now().strftime('%Y-%m-%d')
            procurement_id = procurement.name_create('OS-' + self.work_order_id.order_no + '-' + date)

            # Crear orden de solicitud
            # Verifica de donde coges los valores de los campos 'expected_date' 'warehouse_id' 'default_analytic_account_id'
            # Los coges de las lineas de productos o de la orden en general.
            # if not self.product_ids[0].location:
            #     raise ValidationError(_('You have that get a location'))
            stock_req_order = obj_stock_request_order.sudo().create({
                'expected_date': datetime.now(),  # record.date,  # '2023-05-18 13:54:02',
                'picking_policy': 'one',  # Puede ser el valor 'direct' o 'one'.Recomiendo 'one'
                'warehouse_id': warehouse.id,
                'location_id': self.env.ref('stock.stock_location_customers').id,
                'procurement_group_id': procurement_id[0],  # Procurement creado anteriormente
                'company_id': self.env.user.company_id.id,
                'default_analytic_account_id': self.work_order_id.brigade_cost_center.id,
                'message_follower_ids': [],
                'activity_ids': [],
                'employee_id':self.employee_id.id,
                'order_id':self.work_order_id.id,
                'message_ids': []})

            stock_request_list = []
            for record in products_line:
                stock_req = self.env['stock.request'].create({
                    'product_id': record.product_id.id,  # Producto
                    'product_uom_id': record.product_uom.id,  # Unidad de medida del prducto
                    'route_id': record.env.ref('stock.route_warehouse0_mto').id,
                        # Ruta a seguir self.env.ref('stock.route_warehouse0_mto').id
                    'analytic_account_id': self.work_order_id.brigade_cost_center.id,
                        # Centro de Costo igual al anterior
                    'analytic_tag_ids': [[6, False, []]],
                    'product_uom_qty': record.product_uom_qty,  # Cantidad
                    'expected_date': datetime.now(),  # '2023-05-18 13:54:02',
                    'picking_policy': 'one',  # Puede ser el valor 'direct' o 'one'.Igual al ya especificado
                    'warehouse_id': warehouse.id,  # Almacen definido arriba
                    'location_id': self.env.ref('stock.stock_location_customers').id,
                        # Ubicación definida anteriormente
                    'procurement_group_id': procurement_id[0],  # Procurement creado anteriormente
                    'company_id': self.env.user.company_id.id,
                    'order_id': stock_req_order.id,
                    'work_order_product_id':record.line_product_id.id
                        # 'work_order_product_id': record
                    })

            stock_req_order.action_confirm()
            for product in products_line:
                product.line_product_id.stock_request_order_ids =[(4, stock_req_order.id)]
                product_uom_qty = product.line_product_id.reservation_id.product_uom_qty
                product.line_product_id.reservation_id.write({'product_uom_qty': product_uom_qty - record.product_uom_qty})
                product.line_product_id.product_expected = product.line_product_id.product_expected + product.product_uom_qty

            stock_req_ids.append(stock_req_order.id)


        action_report =  self.env.ref('df_maintenance.action_print_receipt').report_action([], data={'order_id': self.work_order_id.id,
                                                                                               'stock_req_ids':stock_req_ids,
                                                                                               },)
        action_report['close_on_report_download'] = True
        return action_report

class MaintenanceProductExpeditionProducts(models.TransientModel):
    _name = 'df.maintenance.product.expedition.product'

    expedition_id = fields.Many2one('df.maintenance.product.expedition','Expedition ID')
    product_id = fields.Many2one('product.product', string="Product", required=True)
    product_uom_qty = fields.Integer('Cantidad Requerida')
    product_uom = fields.Many2one('uom.uom', string="Product UOM", readonly=True, related='product_id.uom_id')
    limit = fields.Integer('Cantidad Maxima')
    line_product_id = fields.Many2one('df.work.order.product', 'Line Product')
    warehouse_id = fields.Many2one(
        "stock.warehouse",
        "Warehouse",
    )

    @api.onchange('limit', 'product_uom_qty')
    def onchange_product_uom_qty(self):
        for record in self:
            if record.product_uom_qty > record.limit:
                raise ValidationError(_('Don not have that quantity reserved'))



