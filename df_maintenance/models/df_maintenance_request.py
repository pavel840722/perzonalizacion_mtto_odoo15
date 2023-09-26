# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, tools
from odoo.exceptions import UserError, ValidationError
from lxml import etree
import json
import re

class MaintenanceRequest(models.Model):
    _inherit = 'maintenance.request'
    _rec_name = 'request_number'

    @api.model
    def _get_location(self):
        obj_equipment = self.env['df.maintenance.equipment']
        if self.env.context.get('active_id'):
            active_id = self.env.context['active_id']
            return obj_equipment.search([('id', '=', active_id)]).stock_asset_id.id


    @api.model
    def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):
        context = self._context
        res = super(MaintenanceRequest, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        if view_type == 'tree':
            doc = etree.XML(res['arch'])
            for node in doc.xpath("//field[@name='user_id']"):
                    node.set('invisible', '1')
                    modifiers = json.loads(node.get('modifiers', '{}'))
                    modifiers['tree_invisible'] = True
                    modifiers['column_invisible'] = True
                    node.set('modifiers', json.dumps(modifiers))
            res['arch'] = etree.tostring(doc)
        return res


    request_number = fields.Char('Request number', size=16, readonly=True, default=lambda context: '/')
    stock_asset_id = fields.Many2one('df.maintenance.physical.location', string='Asset location',  required=True) #,default = lambda x: x._get_location()
    cost_center = fields.Many2one('account.analytic.account', 'Client',domain="[('id', 'in', cost_center_allowed )]" ,required=True)
    cost_center_allowed = fields.Many2many('account.analytic.account', 'Analytic Account', compute='_compute_cost_center_allowed')
    # workshop_cost_center = fields.Many2one('account.analytic.account', related='maintenance_team_id.analytic_account', string='Workshop Cost Center')
    maintenance_type = fields.Selection([('corrective', 'Corrective'), ('preventive', 'Preventive'), ('support', 'Support'), ('improvement', 'Improvement')],
                                        string='Maintenance Type', default="corrective")
    work_order_ids = fields.One2many('df.maintenance.work.order', 'request_id', string="Work Orders", readonly=True)
    priority_zlc = fields.Selection([('low', 'M8+ / low'), ('normal', 'M1-7 / normal'), ('high', 'M0 / high')], 'Priority', default=lambda self: self.equipment_id.criticality)
    stage_id = fields.Many2one('maintenance.stage', string='Stage', readonly=True)
    is_project = fields.Boolean('Project',  readonly=True)
    workshop_number = fields.Integer('Workshop number',  related='maintenance_team_id.serie')
    subcategory_id = fields.Many2one('df.maintenance.equipment.subcategory', related='equipment_id.subcategory_id', string='Subcategory')
    active = fields.Boolean("Active", default=True)
    warning_request = fields.Boolean(default = False)
    cancellation_reasons = fields.Text(string="Reasons for cancellation",)
    date_cancellation = fields.Date(string="Date of cancellation",)
    request_areas = fields.One2many('df.maintenance.request.area', 'request_id', string='Areas')
    save = fields.Boolean(default=False)
    generate_order_visible = fields.Boolean(default=False)
    mtto_plant = fields.Boolean('Mtto Plant')
    assign_order = fields.Boolean(default=False)
    department_id = fields.Many2one('hr.department', string='Department', domain="[('id', 'in', department_allowed)]")
    department_allowed = fields.Many2many('hr.department', string='Department',compute='_compute_department_allowed')

    @api.onchange('request_areas')
    def _onchange_request_areas(self):
        self.generate_order_visible = True

    @api.depends('cost_center')
    def _compute_department_allowed(self):
        for record in self:
            if record.cost_center and record.mtto_plant==True:
                list = []
                department_ids = self.env['df.maintenance.department.centro'].search([('cost_center', '=', record.cost_center.id)])
                for department_id in department_ids.department:
                    list.append(department_id.id)
                    record.department_allowed = list
            else:
                record.department_allowed = False


    @api.depends('mtto_plant')
    def _compute_cost_center_allowed(self):
        for record in self:
            list = []
            if record.mtto_plant == True:
                center = self.env['account.analytic.account'].search([('code','in',(202,207,203,206,214,212))])
                for index in center:
                    list.append(index.id)
                record.cost_center_allowed = list
            else:
                center = self.env['account.analytic.account'].search([])
                record.cost_center_allowed = center





    @api.model
    def create(self, vals):
        if vals.get('priority_zlc'):
            if vals.get('priority_zlc') == 'low':
                vals['priority'] = '1'
            elif vals.get('priority_zlc') == 'normal':
                vals['priority'] = '2'
            elif vals.get('priority_zlc') == 'high':
                vals['priority'] = '3'
        if not re.match("^[a-zA-ZñáéíóúüÑÁÉÍÓÚÜ\\ \\d]+$", vals.get('name')):
            raise ValidationError(_("You cannot enter strange characters in the name field."))

        if ('request_number' not in vals) or (vals.get('request_number') == '/'):
            vals['request_number'] = self.env['ir.sequence'].get('df.maintenance.request')
        # self.__update_values(vals)
        vals['warning_request'] = False
        vals['save'] = True
        request = super(MaintenanceRequest, self).create(vals)
        # if request.send_email_to_planners and not request.send_email_to_planners:
        #     template = self.env.ref('l10n_cu_maintenance_unexpected.template_new_maintenance_request')
        #     template.send_mail(request.id, force_send=True)

        return request

    def search(self,args, offset=0, limit=None, order=None, count=False):
        equipment_id = mtto_plant = schedule_date = id = 0
        for conditions in args:
            for value in conditions:
                if value == 'mtto_plant':
                    mtto_plant  = 1
                if value == 'schedule_date':
                    schedule_date = 1
                if value == 'id':
                    id = 1
                if value == 'equipment_id':
                    equipment_id = 1

        if len(args) > 0 and self.env.uid == 2 and mtto_plant == 0 and schedule_date==0 and id==0 and equipment_id == 0:
            args = []
        elif mtto_plant == 1 and self.env.uid != 2:
            args.append(('create_uid' ,'=', self.env.uid))
        return super(MaintenanceRequest, self).search(args, offset, limit, order, count)


    def write(self, vals):
        if vals.get('name'):
            if not re.match("^[a-zA-ZñáéíóúüÑÁÉÍÓÚÜ\\ \\d]+$", vals.get('name')):
                raise ValidationError(_("You cannot enter strange characters in the name field."))
        vals['warning_request'] = False
        return super(MaintenanceRequest, self).write(vals)

    def action_order_assign(self):

        if self.mtto_plant == False:
            if len(self.request_areas.ids)==0:
                raise ValidationError(_("You must select at least one workshop and one brigade."))
            order_obj = self.env['df.maintenance.work.order']
            order_act = self.env['df.work.order.activity']
            list_order = []
    
    
            for row in self.request_areas:
                for brigada in row.brigades_ids:
                    if len(order_obj.search([('request_id','=',self.id),('brigade_id','=',brigada.id)])) == 0:
                        # get order data and create order
                        order_data = {
                            'work_type': self.maintenance_type,
                            'asset_id': self.equipment_id.id,
                            'stock_asset_id': self.stock_asset_id.id,
                            'priority': self.priority_zlc,
                            'company_id': self.company_id.id,
                            'request_id': self.id,
                            'maintenance_team_id': row.area_id.id,
                            'brigade_id': brigada.id,
                            'brigade_cost_center':brigada.analytic_account.id
                        }
                        order_id = order_obj.sudo().create(order_data)
    
            action = self.env.ref('df_maintenance.df_action_maintenance_work_order_request')
            domain = [('request_id', '=', self.id)]
            action.sudo().write({'domain':domain})

            result = action.read()[0]
            self.assign_order = True
            self.generate_order_visible = False
            return result

        elif self.mtto_plant == True:
            order_obj = self.env['df.maintenance.work.order']
            order_data = {
                'work_type': self.maintenance_type,
                'asset_id': self.equipment_id.id,
                'stock_asset_id': self.stock_asset_id.id,
                'priority': self.priority_zlc,
                'company_id': self.company_id.id,
                'request_id': self.id,
                'brigade_cost_center':self.cost_center.id,
                'order_plant':True,
                'department_id':self.department_id.id,
            }
            order_id = order_obj.sudo().create(order_data)


            # self.stage_id = 2
            action = self.env.ref('df_maintenance.df_action_maintenance_work_order_to_plant')

            result = action.read()[0]
            self.assign_order = True
            return result



    def action_canceled(self):
        """ Changes request state to canceled.
        :rtype: True
        """
        self.ensure_one()
        res_id = self.env['df.maintenance.request.cancel'].create({'request_id': self.id}).id
        return {
            'name': _('Cancel maintenance order request'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'df.maintenance.request.cancel',
            'res_id': res_id,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    def action_attended(self):
        """ Changes request state to attended.
        :rtype: True
        """
        self.stage_id = 3
        return True

    def action_insolvable(self):
        """ Changes request state to insolvable.
        :rtype: True
        """
        self.stage_id = 4
        return True


    @api.onchange('stock_asset_id')
    def _onchange_stock_asset_id(self):
        if not self.env.context.get('default_cost_center'):
           self.equipment_id = ''

    @api.onchange('cost_center')
    def _onchange_cost_center(self):
        if not self.env.context.get('default_cost_center'):
            self.stock_asset_id = ''
        if self.env['project.project'].search([('analytic_account_id','=',self.cost_center.id)]):
            self.is_project = True
        else:
            self.is_project = False

    @api.onchange('equipment_id')
    def _onchange_equipment_id(self):
        if self.equipment_id.id:
             self.priority_zlc = self.equipment_id.criticality
             if self.search_count([('equipment_id', '=', self.equipment_id.id), ('stage_id', 'in', [1, 2])]) > 0:
                 self.warning_request = True
             else:
                 self.warning_request = False

    def check_orders(self, estado_order):
        terminacion = True
        count_terminado = 0
        for order in self.work_order_ids:
            if order.state == 'free' or order.state == 'in_progress':
                terminacion = False
                break
            elif order.state == 'terminado' or order.state == 'posted':
                count_terminado = count_terminado + 1

        if terminacion == True:
            if estado_order == 'cancelled' and count_terminado == 0:
                self.stage_id = 4
            elif estado_order == 'unfinished':
                self.stage_id = 4
            elif estado_order == 'insolvable':
                self.stage_id = 4
            elif estado_order == 'finished':
                self.stage_id = 3


    def unlink(self):
        for request in self:
            if request.stage_id.id != 1:
                raise ValidationError(_("You cannot delete a request that is already in progress."))
            return super(MaintenanceRequest, self).unlink()