# -*- coding: utf-8 -*-

from odoo import api, fields, models, _, tools
from odoo.addons import decimal_precision as dp
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError

from datetime import datetime
import warnings
from datetime import timedelta
from odoo.osv import expression
import json


class MaintenanceWorkOrder(models.Model):
    _name = 'df.maintenance.work.order'
    _description = "Work Order"
    _inherit = 'mail.thread'
    _rec_name = "order_no"

    def remove_draf_orders(self):
        obj_maintenance_remove_settings = self.env['df.maintenance.remove.settings']
        days_to_remove_order = obj_maintenance_remove_settings.search([])[0].days_to_remove_order
        fecha_actual = datetime.now()
        work_orders = self.search([('state', '=', 'free')])
        list = []
        for record in work_orders:
            fecha_a_comprobar = record.create_date + timedelta(days=days_to_remove_order)
            if fecha_actual >= fecha_a_comprobar:
                list.append(record.id)

        action = self.env["ir.actions.actions"]._for_xml_id(
            "df_maintenance.df_action_maintenance_work_order_archived")

        action["domain"] = [
            ('id', 'in', list)
        ]

        return action


    def post_work_force(self, closing_date):
        account_move_obj = self.env['account.move']
        account_move_line_obj = self.env['account.move.line']
        work_orders = self.search([('state', '!=', 'free')])
        for record in work_orders:
            importe_total = 0
            for employee in record.employee_ids:
                if employee.posted == False and employee.date <= closing_date and employee.amount > 0 and employee.real_time > 0:
                    importe_total = importe_total + employee.amount
                    employee.posted = True
            if importe_total > 0:
                vals_account_move = {}
                vals_account_move['date'] = datetime.now()
                vals_account_move['move_type'] = 'entry'
                if record.request_id.is_project == True:
                    vals_account_move['journal_id'] = self.env['account.journal'].search([('code', '=', 'HRP')]).id
                    vals_account_move['ref'] = 'Horas Contables de Proyectos' + '/' + record.order_no
                else:
                    vals_account_move['journal_id'] = self.env['account.journal'].search([('code', '=', 'HRM')]).id
                    vals_account_move['ref'] = 'Horas Contables de Operación' + '/' + record.order_no
                obj_ids = account_move_obj.create(vals_account_move)
                obj_ids.write({'state': 'posted'})
                # hasta aqui genero el asiento en el modelo:account.move
                valores = []
                vals_account_move_line = {}
                vals_account_move_line['move_id'] = obj_ids.id
                vals_account_move_line['date'] = datetime.now()
                if record.request_id.is_project == True:
                    vals_account_move_line['journal_id'] = self.env['account.journal'].search([('code', '=', 'HRP')]).id
                else:
                    vals_account_move_line['journal_id'] = self.env['account.journal'].search([('code', '=', 'HRM')]).id
                vals_account_move_line1 = {}
                vals_account_move_line1['move_id'] = obj_ids.id
                vals_account_move_line1['date'] = datetime.now()
                if record.request_id.is_project == True:
                    vals_account_move_line['journal_id'] = self.env['account.journal'].search([('code', '=', 'HRP')]).id
                else:
                    vals_account_move_line['journal_id'] = self.env['account.journal'].search([('code', '=', 'HRM')]).id

                if record.request_id.is_project == True:
                    vals_account_move_line['account_id'] = self.env['df.maintenance.accounts'].search([])[0].project.id
                else:
                    vals_account_move_line['account_id'] = self.env['df.maintenance.accounts'].search([])[
                        0].workforce.id
                vals_account_move_line['debit'] = importe_total
                vals_account_move_line['credit'] = 0.0
                vals_account_move_line['balance'] = importe_total
                vals_account_move_line['analytic_account_id'] = record.request_id.cost_center.id
                valores.append(vals_account_move_line)

                if record.request_id.is_project == True:
                    vals_account_move_line1['account_id'] = self.env['df.maintenance.accounts'].search([])[
                        0].service_transfer.id
                else:
                    vals_account_move_line1['account_id'] = self.env['df.maintenance.accounts'].search([])[
                        0].workforce_recovery.id
                vals_account_move_line1['debit'] = 0.0
                vals_account_move_line1['credit'] = importe_total
                vals_account_move_line1['balance'] = -importe_total
                vals_account_move_line1['analytic_account_id'] = record.brigade_id.analytic_account.id
                valores.append(vals_account_move_line1)
                account_move_line_obj.create(valores)

    @api.model
    def _default_picking_type(self):
        type_obj = self.env['stock.picking.type']
        company_id = self.env.context.get('company_id') or self.env.user.company_id.id
        types = type_obj.search([('code', '=', 'incoming'), ('warehouse_id.company_id', '=', company_id)])
        if not types:
            types = type_obj.search([('code', '=', 'incoming'), ('warehouse_id', '=', False)])
        return types[:1]

    @api.depends('product_ids', 'employee_ids')
    def _calc_product_labor_total_amount(self):
        product_amount = 0.00
        labor_amount = 0.00
        for product in self.product_ids:
            product_amount += product.amount
        for employee in self.employee_ids:
            labor_amount += employee.amount
        self.product_amount = product_amount
        self.labor_amount = labor_amount
        self.total_amount = labor_amount + product_amount

    labor_amount = fields.Float(string='Labor amount', readonly=True, digits=(10, 2), store=True,
                                compute=_calc_product_labor_total_amount)
    product_amount = fields.Float(string='Product amount', readonly=True, digits=(10, 2), store=True,
                                  compute=_calc_product_labor_total_amount)
    total_amount = fields.Float(string='Total amount', readonly=True, store=True, digits=(10, 2),
                                compute=_calc_product_labor_total_amount, auto_commit=True)
    order_no = fields.Char('Work Order No.', size=16, readonly=True, default=lambda context: _('New'))
    # create_date = fields.Datetime('Create Date', readonly=True, select=True)
    date_start = fields.Datetime('Start Date')
    date_end = fields.Datetime('End Date')
    date_supervised = fields.Datetime('Supervised Date')
    company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.user.company_id)
    responsible_employee_id = fields.Many2one('hr.employee', 'Responsible')
    comments = fields.Text('Comments')
    activity_ids = fields.One2many('df.work.order.activity', 'order_id', 'Activities')
    product_ids = fields.One2many('df.work.order.product', 'order_id', 'Products')
    product_service_ids = fields.One2many('df.work.order.product.service', 'order_id', 'Services Products')
    employee_ids = fields.One2many('df.work.order.employee', 'order_id', 'Labor')
    supervised_ids = fields.One2many('df.work.order.supervised.history', 'order_id', 'Labor')
    active = fields.Boolean("Active", default=True)

    currency_id = fields.Many2one('res.currency', string='Currency',
                                  default=lambda self: self.env.user.company_id.currency_id)
    completion = fields.Selection([('finished', 'Finished'),
                                   ('unfinished', 'Unfinished'),
                                   ('insolvable', 'Insolvable')],
                                  'Evaluation of supervition')
    work_type = fields.Selection([('preventive', 'Preventive'),
                                  ('corrective', 'Corrective'),
                                  ('support', 'Support'),
                                  ('upgrade', 'Upgrade')],
                                 'Work type', required=True,
                                 help="According the work type selection optional fields will be show in the work order.")
    asset_id = fields.Many2one('maintenance.equipment', string="Maintenance Asset", required=True, index=True)
    stock_asset_id = fields.Many2one('df.maintenance.physical.location', string='Asset location',
                                     required=True)  # ,default = lambda x: x._get_location()
    priority = fields.Selection([('low', 'M8+ / low'), ('normal', 'M1-7 / normal'), ('high', 'M0 / high')], 'Priority',
                                default=lambda *a: 'high')
    state = fields.Selection([('free', 'Free'),
                              ('in_progress', 'In progress'),
                              ('finished', 'Finished'),
                              ('posted', 'Posted'),
                              ('history', 'History'),
                              ('cancelled', 'Cancelled')],
                             'State', required=True, readonly=True, default=lambda *a: 'free',
                             track_visibility='onchange')
    downtime = fields.Float()
    hours = fields.Float(string="Time Spent", compute='_compute_hours')
    verified_employee_id = fields.Many2one('hr.employee', 'Verified By')
    failure_cause_id = fields.Many2one('df.maintenance.failure.cause', 'Failure cause')
    nbr = fields.Integer(string="# of Cases", readonly=True, default=lambda *a: 1)
    performed_employee_id = fields.Many2one('hr.employee', 'Realizado Por', required=False,
                                            default=lambda self: self.env['hr.employee'].search(
                                                [('user_id', '=', self.env.user.id)]).id)

    is_subcontracted = fields.Boolean('Is Subcontracted', default=False)
    # partner_id = fields.Many2one('res.partner', 'Partner')
    # nro_contract = fields.Char('No. Contract')
    # maintenance_cost = fields.Float('Maintenance Cost', digits=dp.get_precision('Account'))
    # total_amount_contracted = fields.Float('Total amount', digits=dp.get_precision('Account'), related='maintenance_cost')
    request_id = fields.Many2one('maintenance.request', 'Request number', readonly=True)
    request_nro = fields.Char('Request number', related='request_id.request_number')
    permanent = fields.Boolean('Permanent', default=False)
    brigade_id = fields.Many2one('df.maintenance.brigade', string='Brigade')
    # department_id = fields.Char('Department', related='brigade_id.department_id.id')
    maintenance_team_id = fields.Many2one('maintenance.team', string='Maintenance area')
    brigade_cost_center = fields.Many2one('account.analytic.account', string='Brigade Cost Center')
    # workshop_cost_center = fields.Many2one('account.analytic.account', related='maintenance_team_id.analytic_account', string='Workshop Cost Center')
    department_id = fields.Many2one('hr.department', string='HR department')
    # deparment_id = fields.Many2one(related='request_id.brigade_id.deparment_id', store=True)
    # observation = fields.Text('Observations Supervise')
    observation_final = fields.Text('Observations Close')
    order_plant = fields.Boolean('Order Plants',defautl=False)
    cc_asset_id_code = fields.Char(related='asset_id.cost_center.code', store=True)
    cc_asset_id = fields.Many2one(related='asset_id.cost_center', store=True)
    asset_id_code = fields.Char(related='asset_id.code', store=True)



    READONLY_STATES = {
        'purchase': [('readonly', True)],
        'done': [('readonly', True)],
        'cancel': [('readonly', True)],
    }

    picking_count = fields.Integer(compute='_compute_picking', string='Receptions', default=0, store=True,
                                   compute_sudo=True)
    picking_ids = fields.Many2many('stock.picking', compute='_compute_picking', string='Receptions', copy=False,
                                   store=True, compute_sudo=True)

    picking_type_id = fields.Many2one('stock.picking.type', 'Deliver To', states=READONLY_STATES, required=True,
                                      default=_default_picking_type,
                                      help="This will determine operation type of incoming shipment")
    group_id = fields.Many2one('procurement.group', string="Procurement Group", copy=False)
    cancellation_reasons = fields.Text(string="Motivos de la cancelación")
    date_cancellation = fields.Date(string="Date of cancellation", )
    request_count = fields.Integer(compute='calc_request')

    employee_validate = fields.Boolean(default = False)
    stock_request_order = fields.One2many('stock.request.order','order_id')
    count_stock_request = fields.Integer('Stock Request', compute='_compute_count_stock_request')

    purchase_ids = fields.One2many('approval.request','work_order_id','Request Purchase')
    count_request_purchase = fields.Integer('Count Request Purchase',compute='_compute_count_request_purchase')

    # archived_show = fields.Boolean(default=False)
    # is_planner = fields.Boolean('Is Planner', compute='is_planner')

    # _sql_constraints = [
    #     ('activity_ids_uniq', 'unique (activity_ids)', "La actividad existe ya !"),
    # ]

    # def check_access_rule(self, operation):
    #     super(MaintenanceWorkOrder, self).check_access_rule(operation)
    #     employee_obj = self.env['hr.employee'].search([('user_id','=',self.env.uid)])
    #     if operation in ('read', 'write', 'unlink') and not self.brigade_id == employee_obj.department_id:
    #        raise AccessError(_('You are not allowed to access this document.'))

    def search(self, args, offset=0, limit=None, order=None, count=False):
        if self.user_has_groups('df_maintenance.group_maintenance_executor') and self.env.uid != 2:
            new_args = []
            for condition in args:
                if condition[0] != 'create_uid':
                    new_args.append(condition)
            args = new_args
            employee_obj = self.env['hr.employee'].sudo().search([('user_id', '=', self.env.uid)])
            if employee_obj.department_id.id:
                args.append(['brigade_id.hr_department.id', '=', employee_obj.department_id.id])

        elif self.env.uid == 2:
            new_args = []
            for condition in args:
                if condition[0] != 'create_uid':
                    new_args.append(condition)
                # if condition[0] == 'request_id' or condition[0] == 'order_no':
            if len(new_args) == 2 and new_args[0][0] == '&':
                new_args = new_args[1]
            args = new_args
        elif self.user_has_groups('df_maintenance.group_maintenance_petitioner') and self.env.uid != 2:
            new_args = []
            for condition in args:
                if condition[0] != 'create_uid':
                    new_args.append(condition)
            args = new_args
            employee_obj = self.env['hr.employee'].sudo().search([('user_id', '=', self.env.uid)])
            request_ids = self.env['maintenance.request'].sudo().search([('employee_id', '=', employee_obj.id)]).ids
            args.append(['request_id', 'in', request_ids])

        return super(MaintenanceWorkOrder, self).search(args, offset, limit, order, count)

    def show_purchase(self):
        action = self.env["ir.actions.actions"]._for_xml_id(
            "approvals.approval_request_action_to_review_category")
        action['domain'] = [('work_order_id', '=', self.id)]
        return action

    @api.depends('product_ids', 'employee_ids')
    def _calc_product_labor_total_amount(self):
        product_amount = 0.00
        labor_amount = 0.00
        for product in self.product_ids:
            product_amount += product.amount
        for employee in self.employee_ids:
            labor_amount += employee.amount
        self.product_amount = product_amount
        self.labor_amount = labor_amount
        self.total_amount = labor_amount + product_amount
        return self.total_amount


    @api.depends('purchase_ids')
    def _compute_count_request_purchase(self):
        for record in self:
            if record.purchase_ids:
                record.count_request_purchase = len(record.purchase_ids)
            else:
                record.count_request_purchase = 0

    @api.depends('stock_request_order')
    def _compute_count_stock_request(self):
        for record in self:
            if record.stock_request_order:
                record.count_stock_request = len(record.stock_request_order)
            else:
                record.count_stock_request = 0

    def stock_request_order_view(self):
        action = self.env["ir.actions.actions"]._for_xml_id(
            "stock_request.stock_request_order_action")
        action['domain'] = [('order_id', '=', self.id)]
        return action


    # @api.onchange('product_ids')
    # def _onchange_product_ids(self):
    #     self.ubication_ids = [1]
    #     pass

    def print_all(self):
        for button in self.product_ids:
            button.print_validate = True

    def print_never(self):
        for button in self.product_ids:
            button.print_validate = False

    def _compute_hours(self):
        for record in self:
            if record.completion and record.state == 'finished' and record.completion == 'finished':
                diferencia = record.date_start - record.date_end
                record.hours = diferencia.total_seconds() / 3600 - record.downtime
            else:
                record.hours = 0



    def expedition_all(self, from_js = None):
        list = []
        warehouse_list = []
        for record in self.product_ids:
            if record.print_validate == True:
                if record.delivery_status in ('reserved','delivey_partial'):
                    if record.product_qty != record.product_expected:
                    # if warehouse[0].store_id.id == record.store_id.id:
                    #     stock_request_incomplete = record.stock_request_order_ids.filtered(lambda r: r.state != 'done')
                    #     if not stock_request_incomplete:

                        vals = (0, 0, {
                                'product_id': record.product_id.id,
                                'product_uom_qty': record.product_qty - record.product_expected,
                                'limit': record.product_qty - record.product_expected,
                                'product_uom': record.product_uom.id,
                                'line_product_id': record.id,
                                'warehouse_id':record.store_id.id
                        })
                        list.append(vals)
                        warehouse_list.append(record.store_id.id)
                    else:
                        raise ValidationError(
                            _('Sorry But this product has all reserves in a expedition'))
                        # else:
                        #     raise ValidationError(_('Can not do other expedition if you have in turned one'))
                    # else:
                    #     raise ValidationError(
                    #         _('You can not  make expedition with warehouse store'))
                else:
                    raise ValidationError(
                        _('Must be in status Reserved all products for may create the expedition'))



        action = self.env["ir.actions.actions"]._for_xml_id(
            "df_maintenance.df_action_product_expedition_wizard")
        action['context'] = {
            'default_warehouse_ids': [(6, 0, warehouse_list)],
            'default_work_order_id': self.id,
            'default_product_ids': list

        }
        # action['views'] = [[False, 'form']]
        return action

    def generate_purchase(self):
        list = []
        for record in self.product_ids:
            existence_validated = False
            if record.print_validate == True:
                if record.delivery_status == 'free':
                    existence = self.env['stock.quant'].search([('product_id', '=', record.product_id.id),
                                                                ('inventory_quantity', '!=', False)])
                    if existence:
                        existence_null = [index.available_quantity == 0 for index in existence]
                        existence_validated = all(existence_null)
                    if len(existence) == 0 or existence_validated:
                        request_purchase_incomplete = record.request_purchase_ids.filtered(lambda r: r.request_status in ('new','pending'))
                        if not request_purchase_incomplete:
                            if record.product_qty > 0:
                                vals_aux = (0, 0, {'product_id': record.product_id.id,
                                                       'description': record.product_id.name,
                                                       'warehouse_id': 1,
                                                       'quantity': record.product_qty,
                                                       'product_uom_id': record.product_uom.id,
                                                        'work_order_product_id':record.id
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

                else:
                    raise ValidationError(
                        _('Sorry, but there are some products in state that in not free'))

        if len(list) > 0:
            approval = self.env['approval.request']
            approval_req = approval.create({
                '__last_update': False,
                'request_owner_id': self.env.user.id,
                'category_id': self.env.ref('approvals_purchase.approval_category_data_rfq').id,
                # No existe ese campo pero si lo hacen es este el codigo q iria
                'account_analytic_id': self.request_id.cost_center.id,
                # cuenta analitica o centro de costo que solicita la compra
                'quantity': 0,
                'reference': self.order_no,
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
                'work_order_id':self.id
            })
            for record in approval_req.product_line_ids:
                record.work_order_product_id.request_purchase_ids = [(4, approval_req.id)]

            action = self.env["ir.actions.actions"]._for_xml_id(
                "approvals.approval_request_action_to_review_category")
            action['domain'] = [('id', '=', approval_req.id)]
            return action

    def current_user(self):
        return self.env.uid

    def calc_request(self):
        self.request_count = self.env['maintenance.request'].search_count([('id', '=', self.request_id.id)])

    def action_open(self):
        if len(self.activity_ids) == 0 and self.order_plant == False:
            raise ValidationError(
                _('You cannot open a work order that does not have at least one activity assigned to it'))
        order_no = self.env['ir.sequence'].get('df.maintenance.work.order')
        if not self.date_start:
            date_start = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.date_start = date_start
        if self._context.get('abrir'):
            self.write({'state': 'in_progress', 'order_no': order_no})
        else:
            self.write({'state': 'free', 'order_no': order_no})  # 'date_start': self.date_start
        self.request_id.stage_id = 2

    @api.model
    def __update_values(self, vals):
        if 'asset_id' in vals:
            obj = self.env['maintenance.equipment'].browse(vals['asset_id'])
            vals.update({'stock_asset_id': obj.stock_asset_id.id})

    @api.model
    def create(self, vals):
        self.__update_values(vals)
        return super(MaintenanceWorkOrder, self).create(vals)

    def write(self, vals):
        self.__update_values(vals)
        if vals.get('date_start'):
            if type(vals.get('date_start')) == datetime:
                vals['date_start'] = str(vals.get('date_start'))
            ds_anno = int(vals['date_start'][0:4])
            ds_mes = int(vals['date_start'][5:7])
            ds_dia = int(vals['date_start'][8:10])
            if datetime(self.create_date.year, self.create_date.month, self.create_date.day) > datetime(ds_anno, ds_mes,
                                                                                                        ds_dia):
                raise ValidationError(_('The create date must be less than or equal to the start date'))

        return super(MaintenanceWorkOrder, self).write(vals)

    def delete_activities(self):
        list_no_delete = []
        for act in self.activity_ids:
            if act.delete == True:
                for acts in self.employee_ids:
                    if acts.activity_id.id == act.activity.id and acts.posted == True:
                        act.delete = False
                        list_no_delete.append(act.activity.name)
                for acts in self.product_ids:
                    if acts.activity_id.id == act.activity.id and acts.delivery_status != 'free':
                        act.delete = False
                        list_no_delete.append(act.activity.name)

        for act in self.activity_ids:
            if act.delete == True:



                for acts in self.employee_ids:
                    if acts.activity_id.id == act.activity.id:
                            acts.unlink()

                for acts in self.product_ids:
                    if acts.activity_id.id == act.activity.id:
                        acts.unlink()


                act.unlink()
                cont = 1
                for act in self.activity_ids:
                    valor = str(cont)
                    act.sequence = valor
                    cont = cont + 1




    @api.onchange('asset_id')
    def onchange_asset_id(self):
        if self.asset_id:
            obj = self.env['maintenance.equipment'].browse([self.asset_id.id])
            # self.stock_asset_id = obj.property_stock_asset
            self.stock_asset_id = obj.stock_asset_id

    @api.onchange('activity_ids')
    def onchange_activity_ids(self):
        cont = 1
        for act in self.activity_ids:
            valor = str(cont)
            act.sequence = valor
            cont = cont + 1
        names = []
        if self.activity_ids:
            for act in self.activity_ids:
                names.append(act.activity.name)
                visited = set()
                dup = {x for x in names if x in visited or (visited.add(x) or False)}
            if len(dup) > 0:
                raise ValidationError(_("This activity is already on this work order."))
            else:
                actividad_vieja = self.env['df.work.order.activity'].search([('activity', '=', act.activity.id),
                                                                             ('order_id', '=', self.ids[0])])
                if actividad_vieja.activity.id != act.activity.id:
                    ids = self.env['df.maintenance.activity'].search([('id', '=', act.activity.id)])
                    lines = []
                    # lines_aux = []
                    # lines_aux_two = []
                    # for product in self.product_ids:
                    #     if product.is_order == False:
                    #         vals_aux = (0, 0, {'product_id': product.product_id, 'product_qty': product.product_qty,
                    #                            'product_uom': product.product_uom, 'price_unit': product.price_unit,
                    #                            'amount': product.amount, 'is_order': product.is_order,
                    #                            'location': product.location,
                    #                            'reserved': product.reserved,
                    #                            'delivery_status': product.delivery_status})
                    #         lines_aux.append(vals_aux)
                    #
                    # for product in self.product_ids:
                    #     if product.is_order == True and product.activity_id.id != act.activity.id:
                    #         vals_aux = (0, 0, {'product_id': product.product_id, 'product_qty': product.product_qty,
                    #                            'product_uom': product.product_uom, 'price_unit': product.price_unit,
                    #                            'amount': product.amount, 'is_order': product.is_order,
                    #                            'location': product.location, 'activity_id': product.activity_id.id,
                    #                            'reserved': product.reserved,
                    #                            'delivery_status': product.delivery_status})
                    #         lines_aux_two.append(vals_aux)

                    # self.product_ids = [(5, 0, 0)]
                    for acti in ids:
                        for product in acti.product_ids:
                            vals = (0, 0, {'product_id': product.product_id, 'product_qty': product.quantity,
                                           'product_uom': product.uom_id, 'price_unit': product.price_unit,
                                           'amount': product.amount, 'is_order': product.is_activity,
                                           'activity_id': acti.id})
                            lines.append(vals)
                    self.product_ids = lines
                    # self.product_ids = lines_aux
                    # self.product_ids = lines_aux_two

                    idsj = self.env['df.maintenance.activity'].search([('id', '=', act.activity.id)])
                    linesp = []
                    # linesp_aux = []
                    # linesp_aux_two = []

                    # for employee in self.employee_ids:
                    #     if employee.is_order == True and employee.activity_id.id != act.activity.id:
                    #         vals = (0, 0, {'job_id': employee.job_id, 'employee_id': employee.employee_id,
                    #                        'time': employee.time,
                    #                        'amount': employee.amount, 'is_order': employee.is_order,
                    #                        'activity_id': employee.activity_id.id,
                    #                        'posted': employee.posted})
                    #         linesp_aux.append(vals)
                    #
                    # for employee in self.employee_ids:
                    #     if employee.is_order == False and employee:
                    #         vals = (0, 0, {'job_id': employee.job_id, 'employee_id': employee.employee_id,
                    #                        'time': employee.time,
                    #                        'amount': employee.amount, 'is_order': employee.is_order,
                    #                        'posted': employee.posted})
                    #         linesp_aux_two.append(vals)

                    # self.employee_ids = [(5, 0, 0)]
                    for acti in idsj:
                        for jobs in acti.job_ids:
                            cantd = jobs.cant_job
                            vals = (0, 0, {'job_id': jobs.job_id, 'planned_time': jobs.time,
                                           'amount': jobs.amount / jobs.cant_job, 'is_order': jobs.is_activity,
                                           'activity_id': acti.id})
                            for i in range(cantd):
                                linesp.append(vals)
                    self.employee_ids = linesp
                    # self.employee_ids = linesp_aux
                    # self.employee_ids = linesp_aux_two

    def _check_can_close(self):
        """
        Validate work order dates and completion fields.
        """
        errors = []
        for order in self:
            if not order.date_start:
                errors.append(_("- Must enter a value to the start date field.\n"))
            if not order.date_supervised:
                errors.append(_("- Must enter a value to the end date field.\n"))
            if not order.completion:
                errors.append(_("- Must select a value for the completion field.\n"))
            for employee in order.employee_ids:
                if not employee.employee_id:
                    errors.append(_("- Must select an employee for each job.\n"))
                    break
            if len(errors):
                raise ValidationError(_("You can not close work order [%s].\n") % order.order_no + ''.join(errors))

    def action_close(self):
        """ Changes order state to close.
        @return: True
        """

        self.date_end = datetime.now()
        self._check_can_close()
        self.state = 'finished'

        if self.completion == 'finished':
            self.request_id.check_orders('finished')
            # self.request_id.stage_id = 3
        elif self.completion == 'unfinished':
            self.request_id.check_orders('unfinished')
            # self.request_id.stage_id = 4
        elif self.completion == 'insolvable':
            self.request_id.check_orders('insolvable')
            # self.request_id.stage_id = 4

        in_progress = 0
        finished = 0
        free = 0
        for order in self.request_id.work_order_ids:
            if order.state == 'in_progress':
                in_progress = 1
            elif order.state == 'finished':
                finished = 1
            elif order.state == 'posted':
                posted = 1
            elif order.state == 'history':
                history = 1
            elif order.state == 'free':
                free = 1
        if finished == 1 and in_progress == 0 and free == 0:
            self.request_id.stage_id = 3

    def action_cancel(self):
        self.ensure_one()
        res_id = self.env['df.maintenance.work.order.cancel'].create({'work_order_id': self.id}).id
        return {
            'name': _('Cancelar orden de trabajo'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'df.maintenance.work.order.cancel',
            'res_id': res_id,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    def verify(self):
        self.ensure_one()
        res_id = self.env['df.supervise.work.order'].create({'work_order_id': self.id}).id
        return {
            'name': _('Supervise work'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'df.supervise.work.order',
            'res_id': res_id,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    def action_view_picking(self):
        '''
        This function returns an action that display existing picking orders of given purchase order ids.
        When only one found, show the picking immediately.
        '''
        action = self.env.ref('stock.action_picking_tree_all')
        result = action.read()[0]

        # override the context to get rid of the default filtering on operation type
        result['context'] = {}
        pick_ids = self.mapped('picking_ids')
        # choose the view_mode accordingly
        if not pick_ids or len(pick_ids) > 1:
            result['domain'] = "[('id','in',%s)]" % (pick_ids.ids)
        elif len(pick_ids) == 1:
            res = self.env.ref('stock.view_picking_form', False)
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = pick_ids.id
        return result

    @api.depends('product_ids.move_ids.returned_move_ids',
                 'product_ids.move_ids.state',
                 'product_ids.move_ids.picking_id')
    def _compute_picking(self):
        for order in self:
            pickings = self.env['stock.picking']
            for line in order.product_ids:
                # We keep a limited scope on purpose. Ideally, we should also use move_orig_ids and
                # do some recursive search, but that could be prohibitive if not done correctly.
                moves = line.move_ids | line.move_ids.mapped('returned_move_ids')
                pickings |= moves.mapped('picking_id')
            order.picking_ids = pickings
            order.picking_count = len(pickings)

    def _get_destination_location(self):
        self.ensure_one()
        # if self.dest_address_id:
        #     return self.dest_address_id.property_stock_customer.id
        return self.picking_type_id.default_location_dest_id.id

    def _prepare_picking(self):
        # if not self.group_id:
        #     self.group_id = self.group_id.create({
        #         'name': self.name,
        #         'partner_id': self.partner_id.id
        #     })
        # if not self.partner_id.property_stock_supplier.id:
        #     raise UserError(_("You must set a Vendor Location for this partner %s") % self.partner_id.name)
        return {
            'picking_type_id': self.picking_type_id.id,
            # 'partner_id': self.partner_id.id,
            'date': self.create_date,
            'origin': self.order_no,
            'location_dest_id': self._get_destination_location(),
            # 'location_id': self._get_destination_location(),
            'location_id': 8,
            'company_id': self.company_id.id,
        }

    # def action_print_receipt(self):
    #     if self.state != 'free':
    #         if self.product_ids:
    #             boolean = False
    #             boolean2 = False
    #             for act in self.product_ids:
    #                 if act.print_validate == True:
    #                     boolean = True
    #             if boolean == True:
    #                 for act in self.product_ids:
    #                     if act.print_validate == True:
    #                         store = act.store_id.lot_stock_id
    #                         break
    #                 for act in self.product_ids:
    #                     if act.print_validate == True and act.store_id.lot_stock_id != store:
    #                         boolean2 = True
    #                     if act.print_validate == True and not act.location:
    #                         raise ValidationError(_("The products must have a location."))
    #                     # if act.print_validate == True and act.reserved == False:
    #                     #     raise ValidationError(_("The products must be reserved before print"))
    #
    #                 if boolean2 == True:
    #                     raise ValidationError(_("The products selected must belong to a single warehouse."))
    #
    #                 return self.env.ref('df_maintenance.action_print_receipt').report_action([],
    #                                                                                          data={'order_id': self.id})
    #             else:
    #                 raise ValidationError(_("You must select a product for can print"))
    #
    #         else:
    #             raise ValidationError(_("You must add a product for can print."))
    #     else:
    #         raise ValidationError(_("For can print, the order can not in state FREE "))



    # def action_verify(self):
    #     for record in self.product_ids:
    #         if record.print_validate == True and record.delivery_status == 'free':
    #             product_id = record.product_id.id
    #             warehouse_ids = self.env['stock.warehouse'].search([])
    #             existence_ids = self.env['stock.quant'].search([('product_id', '=', product_id)])
    #             list = []
    #             list_realy = []
    #             warehouse_unic = {}
    #             list_allowed = []
    #             cantidad = 0
    #             for warehouse in warehouse_ids:
    #                 cont = 0
    #                 for existence in existence_ids:
    #                     if warehouse.lot_stock_id.id == existence.location_id.id:
    #                         cont = cont + existence.available_quantity
    #                 if cont > 0:
    #                     vals_aux = (0, 0, {'warehouse_id': warehouse,
    #                                        'cant': cont
    #                                        })
    #                     list.append(vals_aux)
    #             mayor = 0
    #             if list:
    #                 for index in list:
    #                     if index[2]['cant'] > mayor:
    #                         warehouse_unic = index
    #
    #                 record.write({'location': warehouse_unic[2]['warehouse_id']['lot_stock_id'] })
    #                 record.write({'store_id' : warehouse_unic[2]['warehouse_id'].id})


    def action_verify(self):
        for record in self.product_ids:
            if record.print_validate == True :
                if record.delivery_status == 'free':
                    product_id = record.product_id.id
                    warehouse_ids = self.env['stock.warehouse'].search([])
                    existence_ids = self.env['stock.quant'].search([('product_id', '=', product_id)])
                    list = []
                    list_realy = []
                    warehouse_unic = {}
                    list_allowed = []
                    cantidad = 0
                    for warehouse in warehouse_ids:
                        cont = 0
                        for existence in existence_ids:
                            if warehouse.lot_stock_id.id == existence.location_id.location_id.id:
                                cont = cont + existence.available_quantity
                        if cont > 0:
                            vals_aux = (0, 0, {'warehouse_id': warehouse,
                                               'cant': cont
                                               })
                            list.append(vals_aux)
                    mayor = 0
                    if list:
                        for index in list:
                            if index[2]['cant'] > mayor:
                                warehouse_unic = index
                        # for existence in existence_ids:
                        #     if warehouse_unic[2]['warehouse_id'].lot_stock_id.id == existence.location_id.location_id.id:
                        #         list_allowed.append(existence)
                        # list_allowed = sorted(list_allowed, key=lambda x: x.quantity, reverse=True)

                        # for location in list_allowed:
                        #     if cantidad < record.product_qty:
                        #         cantidad = cantidad + location.quantity
                        #         list_realy.append(location.location_id.id)
                        record.write({'location': warehouse_unic[2]['warehouse_id']['lot_stock_id']})
                        record.write({'store_id' : warehouse_unic[2]['warehouse_id']})
                else:
                    raise ValidationError(_('There are not products in state free'))

    def action_post_services(self):
        pass


    def action_mark_all(self):
        pass

    def action_unmark_all(self):
        pass

    # def action_reserve(self):
    #     obj_stock_request_order = self.env['stock.request.order']
    #     procurement = self.env['procurement.group']
    #     # OS2023051700001 debes generarlo, te propongo sea No de orden seguido de fecha y hora
    #     # Ejemplo: Orden 000001 Fecha:17/06/2023 Hora: 00:15 am daría -> 000001202306170015
    #     procurement_id = procurement.name_create('OS2023051700020')
    #     # Crear orden de solicitud
    #     # Verifica de donde coges los valores de los campos 'expected_date' 'warehouse_id' 'default_analytic_account_id'
    #     # Los coges de las lineas de productos o de la orden en general.
    #     if not self.product_ids[0].location:
    #         raise ValidationError(_('You have that get a location'))
    #     stock_req_order = obj_stock_request_order.sudo().create({
    #         'expected_date': datetime.now(),  # record.date,  # '2023-05-18 13:54:02',
    #         'picking_policy': 'one',  # Puede ser el valor 'direct' o 'one'.Recomiendo 'one'
    #         'warehouse_id': self.store_id.id,
    #         'location_id': self.env.ref('stock.stock_location_customers').id,
    #         'procurement_group_id': procurement_id[0],  # Procurement creado anteriormente
    #         'company_id': self.env.user.company_id.id,
    #         'default_analytic_account_id': self.request_id.cost_center.id,
    #         'message_follower_ids': [],
    #         'activity_ids': [],
    #         'message_ids': []})
    #
    #     stock_request_list = []
    #     for record in self.product_ids:
    #         if record.print_validate and record.reserved == False:
    #             if record.product_qty == 0:
    #                 raise ValidationError(_('You can not do this operation without any products'))
    #             if not record.location:
    #                 raise ValidationError(_('You have that get a location'))
    #             stock_req = self.env['stock.request'].create({
    #                 'product_id': record.product_id.id,  # Producto
    #                 'product_uom_id': record.product_uom.id,  # Unidad de medida del prducto
    #                 'route_id': record.env.ref('stock.route_warehouse0_mto').id,
    #                 # Ruta a seguir self.env.ref('stock.route_warehouse0_mto').id
    #                 'analytic_account_id': record.order_id.request_id.cost_center.id,
    #                 # Centro de Costo igual al anterior
    #                 'analytic_tag_ids': [[6, False, []]],
    #                 'product_uom_qty': record.product_qty,  # Cantidad
    #                 'expected_date': record.date,  # '2023-05-18 13:54:02',
    #                 'picking_policy': 'one',  # Puede ser el valor 'direct' o 'one'.Igual al ya especificado
    #                 'warehouse_id': record.store_id.id,  # Almacen definido arriba
    #                 'location_id': record.env.ref('stock.stock_location_customers').id,
    #                 # Ubicación definida anteriormente
    #                 'procurement_group_id': procurement_id[0],  # Procurement creado anteriormente
    #                 'company_id': 1,
    #                 'order_id': stock_req_order.id,
    #                 # 'work_order_product_id': record
    #             })
    #             # stock_request_list.append((4, stock_req.id))
    #             record.reservation_id = stock_req_order.id
    #             record.reserved = True
    #             record.delivery_status = 'reserved'
    #             # stock_req_order.write({'stock_request_ids': stock_request_list})
    #     stock_req_order.action_confirm()

    def action_reserve(self):

        for record in self.product_ids:
            if record.product_qty == 0:
                raise ValidationError(_('You can not do this operation without any products'))
            if not record.location:
                raise ValidationError(_('You have that get a location'))
            stock_reservation = self.env['stock.reservation']
            stock_reservation_obj = stock_reservation.create({
                'product_id': record.product_id.id,
                'product_uom_qty': record.product_qty,
                'product_uom': record.product_uom.id,
                'name': record.product_id.name,  # '00000000010 PAINT BRUSH,3",FOR ROOF PATCH',
                'date_validity': datetime.now() + timedelta(days=30),
                'company_id': self.env.user.company_id.id,
                'restrict_partner_id': False,
                'location_id': record.store_id.lot_stock_id.id,  # Ubicación donde se está el producto. Ejemplo: 100/Stock
                'location_dest_id': self.env.ref('stock_reserve.stock_location_reservation').id,
                'note': 'product reservation'})
            record.reserved = True
            record.delivery_status = 'reserved'
            record.reservation_id = stock_reservation_obj.id
            stock_reservation_obj.reserve()



class WorkOrderActivity(models.Model):
    _name = "df.work.order.activity"
    _description = "Work Order Activity"

    # def set_default(self):
    #     cont = 1
    #     total = self.env['df.work.order.activity'].search([])
    #     for record in self.activity:
    #         cont = cont + 1
    #     return cont
    sequence = fields.Text('Sequence')
    activity = fields.Many2one('df.maintenance.activity', 'Activity', domain="[('brigade_id', '=', brigade_id )]",
                               required=True)
    done = fields.Boolean('Done', default=lambda *a: False)
    order_id = fields.Many2one('df.maintenance.work.order', 'Work Order', ondelete='cascade', required=True)
    brigade_id = fields.Many2one('df.maintenance.brigade')
    delete = fields.Boolean(default=False)
    validate = fields.Boolean(default=False)
    location_ids = fields.Many2one('stock.quant', string='Ubication')

    @api.onchange('activity')
    def onchange_activity(self):
        for record in self:
            record.brigade_id = record.order_id.brigade_id.id

    # @api.depends('activity')
    # def _compute_sequence(self):
    #     cont = 0
    #     for record in self:
    #         if cont == 0:
    #             record.sequence = 1
    #         else:
    #             record.sequence = 1 + cont
    #         cont = cont + 1

    # @api.onchange('activity')
    # def onchange_activity(self):
    #     # return {'domain':{'activity':[('id','in',self.domain())]}}
    #     # self.sequence = ''
    #
    #     brigade = self.env['df.maintenance.brigade.activity'].search([])
    #     list = []
    #     for record in brigade:
    #         if record.brigade_id.hr_department.name == self.brigade:
    #             list.append(record.activity_id.id)
    #     return {'domain':{'activity':[('id','in',list)]}}


class WorkOrderEmployee(models.Model):
    _name = "df.work.order.employee"
    _description = "Work Order Employee"

    def set_default(self):
        brigade_id = self.order_id.brigade_id.hr_department
        return brigade_id

    brigade_id = fields.Many2one('hr.department', string='Brigade', default=set_default, required=True)
    order_id = fields.Many2one('df.maintenance.work.order', string="Work Order", ondelete='cascade', required=True)
    # order_state = fields.Selection('Order state', related='order_id.state')
    employee_id = fields.Many2one('hr.employee', 'Employee', domain="[('id', 'in', employee_allowed )]")
    employee_allowed = fields.Many2many('hr.employee', 'Employee Alloweed', compute='_compute_employee_allowed')
    employee_code = fields.Char('Code', related='employee_id.code', readonly=True, store=True)
    job_id = fields.Many2one('hr.job', 'Job', required=True, domain="[('id', 'in', job_alowed )]")
    job_alowed = fields.Many2many('hr.job', 'Job Allowed', compute='_compute_job_alowed')
    planned_time = fields.Float('Planned time', readonly=True)
    real_time = fields.Float('Real time')
    amount = fields.Float('Amount', digits=(10, 2), required=True, readonly=True)
    date = fields.Datetime('Date', default=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    month = fields.Integer('Month', default=datetime.now().month)
    posted = fields.Boolean('Posted', readonly=True, default=False)
    is_order = fields.Boolean(default=False)
    # validate_employee = fields.Char(compute ='_compute_employee')
    activity_id = fields.Many2one('df.maintenance.activity', 'Reference',domain="[('id', 'in', activity_allowed )]")
    activity_allowed = fields.Many2many('df.maintenance.activity', compute='_compute_activity_allowed')
    # unique_employee = fields.Char()

    _sql_constraints = [
        ('employee_order_month_uniq', 'unique(employee_id,order_id,month)',
         "An employee cannot appear twice in the same order in a month."),
    ]

    @api.depends('order_id')
    def _compute_activity_allowed(self):
        for record in self:
            list = []
            if record.order_id.order_plant == True:
                activity_ids = self.env['df.maintenance.activity'].search(
                    [('department_id', '=', record.order_id.department_id.id)])
                for index in activity_ids:
                    list.append(index.id)
                record.activity_allowed = list
            else:
                activity_ids = self.env['df.maintenance.activity'].search(
                    [('department_id', '=', record.brigade_id.id)])
                for index in activity_ids:
                    list.append(index.id)
                record.activity_allowed = list

    @api.depends('order_id')
    def _compute_job_alowed(self):
        for record in self:
            list = []
            if record.order_id.order_plant == True:
                job_ids = self.env['hr.job'].search([('department_id', '=', record.order_id.department_id.id)])
                for index in job_ids:
                    list.append(index.id)
                record.job_alowed = list
            else:
                job_ids = self.env['hr.job'].search([('department_id', '=', record.brigade_id.id)])
                for index in job_ids:
                    list.append(index.id)
                record.job_alowed = list

    @api.depends('job_id')
    def _compute_employee_allowed(self):
        for record in self:
            list = []
            if record.order_id.order_plant == True:
                employee_ids = self.env['hr.employee'].search(
                    [('job_id', '=', record.job_id.id), ('department_id', '=', record.order_id.department_id.id)])
                for index in employee_ids:
                    list.append(index.id)
                record.employee_allowed = list
            else:
                employee_ids = self.env['hr.employee'].search(
                    [('job_id', '=', record.job_id.id), ('department_id', '=', record.brigade_id.id)])
                for index in employee_ids:
                    list.append(index.id)
                record.employee_allowed = list

    @api.onchange('date')
    def _onchange_date(self):
        self.month = self.date.month

    @api.onchange('job_id')
    def _onchange_job_id(self):
        jobs = self.env['hr.job'].search([])
        self.employee_id = False

        list = []
        for record in self:
            record.brigade_id = self.order_id.brigade_id.hr_department
            # record.unique_employee = ''
            if record.employee_id:
                for aux in jobs:
                    if aux.job_id == record.job_id and aux.employee_ids:
                        for post in aux.employee_ids:
                            list.append(post.name)
                if not record.employee_id.name in list:
                    record.employee_id = False

    @api.onchange('employee_id')
    def _onchange_employee(self):
        if self.employee_id:
            line_employee_id = self.search(
                [('order_id','=', self.order_id.ids[0]), ('employee_id','=', self.employee_id.id),
                 ('month','=', self.date.month)])
            if line_employee_id:
                self.employee_id = ''
                return {'warning':
                    {
                        # 'title': _('Employee twice'),
                        'message': _('It is not possible to select an employee twice in the same month'),
                    }}
            order_work = self.env['df.maintenance.work.order'].search(
                [('id', '!=', self.order_id.ids[0]), ('active', '!=', False), ('state', 'in', ('in_progress', 'free'))])
            for record in order_work:
                # if record.active != False and record.state == 'in_progress' or record.state == 'free':
                for aux in record.employee_ids:
                    if self.employee_id and aux.employee_id == self.employee_id:
                        return {'warning':
                            {
                                'title': _('Employee ocupped'),
                                'message': _('This employee is in other(s) acttivity '),
                            }}



    @api.onchange('job_id', 'real_time')
    def _onchange_amount(self):
        rate = self.env['df.maintenance.rate'].search([('job_id', '=', self.job_id.id)])
        self.amount = rate.hourly_rate * self.real_time

    _sql_constraints = [('employee_job_uniq', 'unique(order_id, employee_id, job_id)',
                         'The employee and job combination of values must be unique in a work order.')]

    def unlink(self):
        for record in self:
            if record.posted == True:
                raise ValidationError(
                    _('You cannot delete a human resource that the amount of hours worked has already been posted'))
            super(WorkOrderEmployee, record).unlink()
        return 1

class AccountMove(models.Model):
    _inherit = "account.move"

    work_order_product_id = fields.Many2one('df.work.order.product')

class WorkOrderProduct(models.Model):
    _name = "df.work.order.product"
    _description = "Work Order Product"

    @api.onchange('price_unit', 'product_qty')
    def _calc_amount_onchange(self):
        self.amount = self.price_unit * self.product_qty

    @api.depends('order_id')
    def _compute_activity_allowed(self):
        for record in self:
            list = []
            if record.order_id.order_plant == True:
                activity_ids = self.env['df.maintenance.activity'].search(
                    [('department_id', '=', record.order_id.department_id.id)])
                for index in activity_ids:
                    list.append(index.id)
                record.activity_allowed = list
            else:
                activity_ids = self.env['df.maintenance.activity'].search(
                    [('department_id', '=', record.order_id.brigade_id.hr_department.id)])
                for index in activity_ids:
                    list.append(index.id)
                record.activity_allowed = list

    price_unit = fields.Float('Unit Price', digits=(10, 2), required=True, readonly=True,
                              related='product_id.standard_price')
    # amount = fields.Float(string='Amount', readonly=True, digits=(10, 2), compute=_calc_amount, store=True)
    amount = fields.Float(string='Amount', readonly=True, digits=(10, 2))
    product_uom = fields.Many2one('uom.uom', string="Product UOM", readonly=True, related='product_id.uom_id')
    product_id = fields.Many2one('product.product', string="Product", required=True,
                                 domain="[('detailed_type','!=','service')]")
    # product_req = fields.Float('Quantity Req', required=True, default=0.0)
    product_qty = fields.Float('Product Qty Solicited', required=True, default=0.0)
    order_id = fields.Many2one('df.maintenance.work.order', string="Work Order", ondelete='cascade', required=True)
    move_ids = fields.One2many('stock.move', 'work_order_product_id', string='Reservation', readonly=True,
                               ondelete='set null', copy=False)
    move_dest_ids = fields.One2many('stock.move', 'created_work_order_product_id', 'Downstream Moves')
    date = fields.Datetime('Date', default=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    delivery_status = fields.Selection([('free', 'Free'),
                                         ('reserved', 'Reserved'),
                                         ('delivey_partial', 'Delivery Partial'),
                                         ('delivered', 'Delivered')]
        , string='Status', default="free", readonly=True)

    print_validate = fields.Boolean(default=False)
    is_order = fields.Boolean(default=False)
    store_id = fields.Many2one('stock.warehouse', string='Store')
    location = fields.Many2many('stock.location', string='Ubication')
    transfer = fields.Boolean(default=False)
    reserve = fields.Boolean('Reserve', default=False)
    reserved = fields.Boolean('Reserved', default=False)
    activity_id = fields.Many2one('df.maintenance.activity', 'Reference',domain="[('id', 'in', activity_allowed )]")
    activity_allowed = fields.Many2many('df.maintenance.activity', 'Reference',compute='_compute_activity_allowed')
    complete_order = fields.Boolean('Complete order', default=False)
    product_qty_delivered = fields.Float('Quanty Delivered',compute='_compute_product_qty_delivered')
    state = fields.Selection([('free', 'Free'),
                              ('in_progress', 'In progress'),
                              ('finished', 'Finished'),
                              ('posted', 'Posted'),
                              ('history', 'History'),
                              ('cancelled', 'Cancelled')],
                             'State', compute='_compute_state')
    reservation_id = fields.Many2one('stock.reservation', string='Reservation')
    account_move_ids = fields.One2many('account.move', 'work_order_product_id', 'Accounting entries')
    stock_request_order_ids = fields.Many2many('stock.request.order',string='Stock request order')
    request_purchase_ids = fields.Many2many('approval.request',string='Request Purchase')
    product_expected = fields.Float('Expected')

    # def unlink(self, context=None):
    #     for record in self:
    #         if record.delivery_status != 'free':
    #             raise ValidationError(_('Can not delete this register if it is in state different of free'))
    #         else:
    #             result = super(WorkOrderProduct, record).unlink()

    def generate_purchase(self):
        list = []
        for record in self:
            existence_validated = False
            # if record.print_validate == True:
            if record.delivery_status == 'free':
                existence = self.env['stock.quant'].search([('product_id', '=', record.product_id.id),
                                                            ('inventory_quantity', '!=', False)])
                if existence:
                    existence_null = [index.available_quantity == 0 for index in existence]
                    existence_validated = all(existence_null)
                if len(existence) == 0 or existence_validated:
                    request_purchase_incomplete = record.request_purchase_ids.filtered(lambda r: r.request_status in ('new','pending'))
                    if not request_purchase_incomplete:
                        if record.product_qty > 0:
                            vals_aux = (0, 0, {'product_id': record.product_id.id,
                                                   'description': record.product_id.name,
                                                   'warehouse_id': 1,
                                                   'quantity': record.product_qty,
                                                   'product_uom_id': record.product_uom.id,
                                                    'work_order_product_id':record.id
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

            else:
                raise ValidationError(
                    _('Sorry, but there are some products in state that in not free'))

        if len(list) > 0:
            approval = self.env['approval.request']
            approval_req = approval.create({
                '__last_update': False,
                'request_owner_id': self.env.user.id,
                'category_id': self.env.ref('approvals_purchase.approval_category_data_rfq').id,
                # No existe ese campo pero si lo hacen es este el codigo q iria
                'account_analytic_id': self.order_id.request_id.cost_center.id,
                # cuenta analitica o centro de costo que solicita la compra
                'quantity': 0,
                'reference': self.order_id.order_no,
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
                'work_order_id':self.order_id.id
            })
            for record in approval_req.product_line_ids:
                record.work_order_product_id.request_purchase_ids = [(4, approval_req.id)]

            action = self.env["ir.actions.actions"]._for_xml_id(
                "approvals.approval_request_action_to_review_category")
            action['domain'] = [('id', '=', approval_req.id)]
            return action


    def expedition_all(self, from_js = None):
        list = []
        warehouse_list = []
        for record in self:
            # if record.print_validate == True:
            if record.delivery_status in ('reserved','delivey_partial'):
                if record.product_qty != record.product_expected:
                    vals = (0, 0, {
                            'product_id': record.product_id.id,
                            'product_uom_qty': record.product_qty - record.product_expected,
                            'limit': record.product_qty - record.product_expected,
                            'product_uom': record.product_uom.id,
                            'line_product_id': record.id,
                            'warehouse_id':record.store_id.id
                    })
                    list.append(vals)
                    warehouse_list.append(record.store_id.id)
                else:
                    if from_js == True:
                        return "all_in_expedition"
                    else:
                        raise ValidationError(
                            _('Sorry But this product has all reserves in a expedition'))
            else:
                if from_js == True:
                    return "must_be_reserved"
                else:
                    raise ValidationError(
                        _('Must be in status Reserved all products for may create the expedition'))

        action = self.env["ir.actions.actions"]._for_xml_id(
            "df_maintenance.df_action_product_expedition_wizard")
        action['context'] = {
            'default_warehouse_ids': [(6, 0, warehouse_list)],
            'default_work_order_id': self.order_id.id,
            'default_product_ids': list
        }
        return action

    def action_verify(self):
        for record in self:
            if record.delivery_status == 'free':
                product_id = record.product_id.id
                warehouse_ids = self.env['stock.warehouse'].search([])
                existence_ids = self.env['stock.quant'].search([('product_id', '=', product_id)])
                list = []
                list_realy = []
                warehouse_unic = {}
                list_allowed = []
                cantidad = 0
                for warehouse in warehouse_ids:
                    cont = 0
                    for existence in existence_ids:
                        if warehouse.lot_stock_id.id == existence.location_id.location_id.id:
                            cont = cont + existence.available_quantity
                    if cont > 0:
                        vals_aux = (0, 0, {'warehouse_id': warehouse,
                                           'cant': cont
                                           })
                        list.append(vals_aux)
                mayor = 0
                if list:
                    for index in list:
                        if index[2]['cant'] > mayor:
                            warehouse_unic = index
                    record.write({'location': warehouse_unic[2]['warehouse_id']['lot_stock_id']})
                    record.write({'store_id' : warehouse_unic[2]['warehouse_id']})

            else:
                return "not_product_free"
                # raise ValidationError(_('There are not products in state free'))
        return "success"

    @api.depends('product_qty','product_qty_delivered')
    def onchange_delivery_status(self):
        for record in self:
            if record.product_qty != 0:
                if record.product_qty_delivered == record.product_qty:
                    record.delivery_status = 'delivered'
                elif record.product_qty_delivered > 0:
                    record.delivery_status = 'delivey_partial'

    # @api.model
    # def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
    #     res = super(WorkOrderProduct, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
    #                                               submenu=submenu)


    @api.depends('order_id.state')
    def _compute_state(self):
        for record in self:
            record.state = record.order_id.state


    @api.depends('stock_request_order_ids')
    def _compute_product_qty_delivered(self):
        for record in self:
            count = 0
            # if record.id.origin:
            #     request_order = self.env['stock.request'].search([('state','=','done'),'|',
            #                                                   ('work_order_product_id','=',record.id.origin),('work_order_product_id','=',record.id)])
            # else:
            #     request_order = self.env['stock.request'].search([('state', '=', 'done'), '|',
            #                                                       ('work_order_product_id', '=', record.id.origin),
            #                                                       ('work_order_product_id', '=', record.id)])
            if record.stock_request_order_ids:
                for stock_request in record.stock_request_order_ids:
                    if stock_request.state == 'done':
                        for line in stock_request.stock_request_ids:
                            if line.work_order_product_id.id == record.ids[0]:
                                count = count + line.qty_done
                record.product_qty_delivered = count
                if record.product_qty_delivered > 0 and not record.product_qty_delivered == record.product_qty:
                    record.delivery_status = 'delivey_partial'
                elif record.product_qty_delivered > 0 and record.product_qty_delivered == record.product_qty:
                    record.delivery_status = 'delivered'
            else:
                record.product_qty_delivered = 0
                # if request_order:
                #     for line in request_order:
                #         count = count + line.qty_done
                #     record.product_qty_delivered = count
                # else:
                #     record.product_qty_delivered = 0


    def expedition(self):
        list_warehouse = []
        if self.product_expected != self.product_qty:
            list = []
            vals = (0, 0, {
                'product_id': self.product_id.id,
                'product_uom_qty':self.product_qty - self.product_expected,
                'limit':self.product_qty - self.product_expected,
                'product_uom': self.product_uom.id,
                'line_product_id': self.id,
                'warehouse_id': self.store_id.id
            })

            list.append(vals)
            list_warehouse.append(self.store_id.id)
            action = self.env["ir.actions.actions"]._for_xml_id(
                "df_maintenance.df_action_product_expedition_wizard")
            action['context'] = {
                'default_warehouse_ids': [(6, 0, list_warehouse)],
                'default_work_order_id':self.order_id.id,
                'default_product_ids':list

            }
            return action
        else:
            raise ValidationError(_('Sorry But this product has all reserves in a expedition'))


    def check_exists(self):
        self.ensure_one()
        res_id = self.env['df.maintenance.product.check.exists'].create({'product_exist_id': self.id}).id
        return {
            'name': _('Check Exists'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'df.maintenance.product.check.exists',
            'res_id': res_id,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    @api.onchange('location')
    def onchange_location(self):
        if self.location:
            if self.location.quantity < self.product_qty:
                self.location = False
                raise ValidationError(_('There are not enough quanty of products in this location'))

    @api.model
    def create(self, vals):
        vals['amount'] = vals['product_qty'] * self.env['product.product'].browse(vals['product_id']).standard_price
        return super(WorkOrderProduct, self).create(vals)

    @api.model
    def write(self, vals):
        vals['amount'] = self.product_qty * self.price_unit
        return super(WorkOrderProduct, self).write(vals)

    def _create_or_update_picking(self):
        for line in self:
            if line.product_id.type in ('product', 'consu'):
                # Prevent decreasing below received quantity
                if float_compare(line.product_qty, line.qty_received, line.product_uom.rounding) < 0:
                    raise UserError('You can not decrease the ordered quantity below the received quantity.\n'
                                    'Create a return first.')

                if float_compare(line.product_qty, line.qty_invoiced, line.product_uom.rounding) == -1:
                    # If the quantity is now below the invoiced quantity, create an activity on the vendor bill
                    # inviting the user to create a refund.
                    activity = self.env['mail.activity'].sudo().create({
                        'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                        'note': _(
                            'The quantities on your purchase order indicate less than billed. You should ask for a refund. '),
                        'res_id': line.invoice_lines[0].invoice_id.id,
                        'res_model_id': self.env.ref('account.model_account_invoice').id,
                    })
                    activity._onchange_activity_type_id()

                # If the user increased quantity of existing line or created a new line
                pickings = line.order_id.picking_ids.filtered(
                    lambda x: x.state not in ('done', 'cancel') and x.location_dest_id.usage in ('internal', 'transit'))
                picking = pickings and pickings[0] or False
                if not picking:
                    res = line.order_id._prepare_picking()
                    picking = self.env['stock.picking'].create(res)
                move_vals = line._prepare_stock_moves(picking)
                for move_val in move_vals:
                    self.env['stock.move'].create(move_val)._action_confirm()._action_assign()

    def _prepare_stock_moves(self, picking):
        """ Prepare the stock moves data for one order line. This function returns a list of
        dictionary ready to be used in stock.move's create()
        """
        self.ensure_one()
        res = []
        if self.product_id.type not in ['product', 'consu']:
            return res
        qty = 0.0
        # price_unit = self._get_stock_move_price_unit()
        price_unit = self.price_unit
        # for move in self.move_ids.filtered(
        #         lambda x: x.state != 'cancel' and not x.location_dest_id.usage == "supplier"):
        #     qty += move.product_uom._compute_quantity(move.product_uom_qty, self.product_uom, rounding_method='HALF-UP')
        template = {
            'name': '',
            'product_id': self.product_id.id,
            'product_uom': self.product_uom.id,
            'date': self.order_id.create_date,
            'date_expected': self.order_id.create_date,
            'location_id': 8,
            'location_dest_id': self.order_id._get_destination_location(),
            'picking_id': picking.id,
            # 'partner_id': self.order_id.dest_address_id.id,
            'move_dest_ids': [(4, x) for x in self.move_dest_ids.ids],
            'state': 'free',
            'work_order_product_id': self.id,
            'company_id': self.order_id.company_id.id,
            'price_unit': price_unit,
            'picking_type_id': self.order_id.picking_type_id.id,
            'group_id': self.order_id.group_id.id,
            'origin': self.order_id.order_no,
            'route_ids': self.order_id.picking_type_id.warehouse_id and [
                (6, 0, [x.id for x in self.order_id.picking_type_id.warehouse_id.route_ids])] or [],
            'warehouse_id': self.order_id.picking_type_id.warehouse_id.id,
            'product_uom_qty': self.product_qty,

        }
        res.append(template)
        return res

    def _create_stock_moves(self, picking):
        moves = self.env['stock.move']
        done = self.env['stock.move'].browse()
        for line in self:
            for val in line._prepare_stock_moves(picking):
                done += moves.create(val)
        return done


    def action_reserve(self, from_js = None):
        for record in self:
            if record.reserved == False:
                if record.product_qty == 0:
                    if from_js == True:
                        return "without_products"
                    else:
                        raise ValidationError(_('You can not do this operation without any products'))
                if not record.location:
                    if from_js == True:
                        return "without_location"
                    else:
                        raise ValidationError(_('You have that get a location'))
                stock_reservation = self.env['stock.reservation']
                stock_reservation_obj = stock_reservation.create({
                    'product_id': record.product_id.id,
                    'product_uom_qty': record.product_qty,
                    'product_uom': record.product_uom.id,
                    'name': record.product_id.name,
                    'date_validity': datetime.now() + timedelta(days=30),
                    'company_id': self.env.user.company_id.id,
                    'restrict_partner_id': False,
                    'location_id': record.store_id.lot_stock_id.id,  # Ubicación donde se está el producto. Ejemplo: 100/Stock
                    'location_dest_id': self.env.ref('stock_reserve.stock_location_reservation').id,
                    'note': 'product reservation'})
                record.reserved = True
                record.delivery_status = 'reserved'
                record.reservation_id = stock_reservation_obj.id
                stock_reservation_obj.reserve()
            else:
                if from_js == True:
                    return "reserved"
                else:
                    raise ValidationError(_('There products must be in free state'))

    # def action_reserve(self):
    #     if self.product_qty == 0:
    #         raise ValidationError(_('You can not do this operation without any products'))
    #     if not self.location:
    #         raise ValidationError(_('You have that get a location'))
    #     stock_reservation = self.env['stock.reservation']
    #     stock_reservation_obj = stock_reservation.create({
    #         'product_id': self.product_id.id,
    #         'product_uom_qty': self.product_qty,
    #         'product_uom': self.product_uom.id,
    #         'name': self.product_id.name,  # '00000000010 PAINT BRUSH,3",FOR ROOF PATCH',
    #         'date_validity': datetime.now() + timedelta(days=30),
    #         'company_id': self.env.user.company_id.id,
    #         'restrict_partner_id': False,
    #         'location_id': self.store_id.lot_stock_id.id,  # Ubicación donde se está el producto. Ejemplo: 100/Stock
    #         'location_dest_id': self.env.ref('stock_reserve.stock_location_reservation').id,
    #         'note': 'product reservation'})
    #     self.reserved = True
    #     self.delivery_status = 'reserved'
    #     self.reservation_id = stock_reservation_obj.id
    #     stock_reservation_obj.reserve()


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    def name_get(self):
        result = []
        for record in self:
            if self.env.context.get('hide_code', True):
                name_show = record.location_id.name
                result.append((record.id, name_show))

            else:
                name_hide = record.product_id.code + ' ' + record.product_id.name
                result.append((record.id, name_hide))

        return result


class WorkOrderSupervisedHistory(models.Model):
    _name = "df.work.order.supervised.history"

    order_id = fields.Many2one('df.maintenance.work.order', 'Work Order', ondelete='cascade', required=True)
    verified_employee_id = fields.Many2one('hr.employee', 'Verified By')
    completion = fields.Selection([('finished', 'Finished'),
                                   ('unfinished', 'Unfinished'),
                                   ('insolvable', 'Insolvable')],
                                  'Evaluation of supervition')
    date_supervised = fields.Datetime('Supervised Date')
    observation = fields.Text('Observations')
    causes_not_finished = fields.Selection([('more_time', 'Ejecution for more time'),
                                            ('missing_parts', 'Lack of Spare Parts'),
                                            ('work_error', 'Work Incorrect')],
                                           'Causes Not Finished')


class WorkOrderProductService(models.Model):
    _name = "df.work.order.product.service"
    _description = "Work Order Product Service"

    @api.onchange('price_unit', 'product_qty')
    def _calc_amount_onchange(self):
        self.amount = self.price_unit * self.product_qty

    product_id = fields.Many2one('product.product', string="Product", required=True,
                                 domain="[('detailed_type','=','service')]")
    price_unit = fields.Float('Unit Price', digits=(10, 2), required=True, readonly=True,
                              related='product_id.standard_price')
    product_qty = fields.Float('Product Qty Solicited', required=True, default=0.0)
    amount = fields.Float(string='Amount', readonly=True, digits=(10, 2))
    contracted_company = fields.Char('Contracted company', readonly=True)
    order_id = fields.Many2one('df.maintenance.work.order', string="Work Order", ondelete='cascade', required=True)
    contract_nro = fields.Char('Contract number', readonly=True)
    post_validate = fields.Boolean('Post', default=False)

    def action_post_service(self):
        pass
