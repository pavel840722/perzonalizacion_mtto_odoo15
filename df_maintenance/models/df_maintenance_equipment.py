# -*- coding: utf-8 -*-

from odoo import api, fields, models, _, tools
from odoo.exceptions import ValidationError
import datetime

class MaintenanceEquipment(models.Model):
    _inherit = ['maintenance.equipment', 'image.mixin']
    _name = "maintenance.equipment"

    def name_get(self):
        result = []
        for record in self:
            if record.name and record.asset_number:
                result.append((record.id, record.name + '/' + record.asset_number))
            if record.name and not record.asset_number:
                result.append((record.id, record.name))
        return result

    code = fields.Char(string='Posición', size=16, copy=False)
    stock_asset_id = fields.Many2one('df.maintenance.physical.location', string='Asset location')
    criticality = fields.Selection(
        [('low', 'M8+ / low'), ('normal', 'M1-7 / normal'), ('high', 'M0 / high')],
        string='Criticality', default='high')
    active = fields.Boolean("Active")
    is_maintenance = fields.Boolean("Maintenance object")
    attribute_ids = fields.One2many('df.resource.attribute', 'asset_id', 'Attributes')
    product_ids = fields.One2many('df.maintenance.object.product', 'asset_id', 'Spare parts')
    asset_number = fields.Char(string='No. Activo')
    manufacturer_id = fields.Many2one('res.partner', string='Manufacturer')
    warranty_start_date = fields.Date(string='Warranty start')
    purchase_date = fields.Date(string='Purchase date')
    work_order_count = fields.Integer(compute='calc_work_order')
    warranty_date = fields.Date('Warranty expiration date')
    period = fields.Integer('Days between each preventive maintenance')
    account_asset_id = fields.Many2one('account.asset', string='Accounting asset')
    maintenance_template_id = fields.Many2one('df.maintenance.template', 'Maintenance Template')
    regimen = fields.Selection(related='maintenance_template_id.regimen')
    subcategory_id = fields.Many2one('df.maintenance.equipment.subcategory', 'Subcategory')
    # analytic_account_number = fields.Char(related='stock_asset_id.analytic_account.code')
    cost_center = fields.Many2one('account.analytic.account', 'Analytic Account', required=True)

    # reading_ids = fields.One2many('df.reading.record', 'resource_id', 'Meter Reading', readonly=True)
    # schedule_ids = fields.One2many('df.maintenance.schedule', 'object_id', 'Schedule')
    # schedule_count = fields.Integer(compute='calc_schedule')

    _sql_constraints = [('serial_no_uniq', 'unique(serial_no)',
                         'The serial number must be unique.')]


    # def action_context(self):
    #     return {
    #         'name': _('Cancel maintenance order request'),
    #         'view_type': 'form',
    #         'view_mode': 'form',
    #         'res_model': 'maintenance.request',
    #         'type': 'ir.actions.act_window',
    #         'target': 'new',
    #         'context': {'default_cost_center': self.cost_center.id,
    #                     'default_stock_asset_id': self.stock_asset_id.id,
    #                     'default_equipment_id': self.id
    #                     }
    #     }

    # def search(self, args, offset=0, limit=None, order=None, count=False):
    #     # args = []
    #     return super(MaintenanceEquipment, self).search(args, offset, limit, order, count)

    def calc_work_order(self):
        self.work_order_count = self.env['df.maintenance.work.order'].search_count([('asset_id', '=', self.id)])



    def validar_annos(self, anno, anno_actual):
        if anno > anno_actual:
            return 1

    @api.onchange('account_asset_id')
    def onchange_asset_id(self):
        if self.account_asset_id:
           self.name = self.account_asset_id.name
           self.cost = self.account_asset_id.original_value
           self.purchase_date = self.account_asset_id.acquisition_date

    @api.onchange('stock_asset_id')
    def onchange_stock_asset_id(self):
        count_analy = self.env['df.maintenance.physical.location'].search([])
        for record in count_analy:
            if record.name == self.stock_asset_id.name:
                self.cost_center = record.analytic_account



    @api.onchange('category_id')
    def _onchange_category_id(self):
        self.subcategory_id = ''


    @api.model
    def create(self, vals):
       fecha_actual_anno = datetime.datetime.now().year
       if vals.get('warranty_date'):
           wd_anno = int(vals['warranty_date'][0:4])
           wd_mes = int(vals['warranty_date'][5:7])
           wd_dia = int(vals['warranty_date'][8:])
           if self.validar_annos(wd_anno, fecha_actual_anno) == 1:
               raise ValidationError(_('The year must not be greater than the current year in the field warranty_date'))
       if vals.get('warranty_start_date'):
           wsd_anno = int(vals['warranty_start_date'][0:4])
           wsd_mes = int(vals['warranty_start_date'][5:7])
           wsd_dia = int(vals['warranty_start_date'][8:])
           if self.validar_annos(wsd_anno, fecha_actual_anno) == 1:
               raise ValidationError(_('The year must not be greater than the current year in the field warranty_start_date'))
       if vals.get('effective_date'):
           if self.validar_annos(int(vals['effective_date'][0:4]), fecha_actual_anno) == 1:
               raise ValidationError(_('The year must not be greater than the current year in the field effective_date'))

       if vals.get('warranty_date') and vals.get('warranty_start_date'):
           if datetime.datetime(wsd_anno, wsd_mes, wsd_dia) > datetime.datetime(wd_anno, wd_mes, wd_dia):
               raise ValidationError(_('The warranty start date must be less than the expiration date'))

       return super(MaintenanceEquipment, self).create(vals)

    def write(self, vals):
       fecha_actual_anno = datetime.datetime.now().year
       if vals.get('warranty_date'):
           wd_anno = int(vals['warranty_date'][0:4])
           wd_mes = int(vals['warranty_date'][5:7])
           wd_dia = int(vals['warranty_date'][8:])
           if self.validar_annos(wd_anno, fecha_actual_anno) == 1:
               raise ValidationError(_('The year must not be greater than the current year in the field warranty_date'))
       if vals.get('warranty_start_date'):
           wsd_anno = int(vals['warranty_start_date'][0:4])
           wsd_mes = int(vals['warranty_start_date'][5:7])
           wsd_dia = int(vals['warranty_start_date'][8:])
           if self.validar_annos(wsd_anno, fecha_actual_anno) == 1:
               raise ValidationError(_('The year must not be greater than the current year in the field warranty_start_date'))
       if vals.get('effective_date'):
           if self.validar_annos(int(vals['effective_date'][0:4]), fecha_actual_anno) == 1:
               raise ValidationError(_('The year must not be greater than the current year in the field effective_date'))

       if vals.get('warranty_date') and vals.get('warranty_start_date'):
           if datetime.datetime(wsd_anno, wsd_mes, wsd_dia) > datetime.datetime(wd_anno, wd_mes, wd_dia):
               raise ValidationError(_('The warranty start date must be less than the expiration date'))

       return super(MaintenanceEquipment, self).write(vals)

    def action_remove(self):
        """
        Removes schedule of maintenance for Maintenance Object (Technical File).
        """
        self.schedule_ids.unlink()
        self.reading_ids.write(dict(next_maintenance_value=None, df_resource_id=False))

        self.write(dict(maintenance_template_id=False))


    @api.onchange('category_id')
    def onchange_category_id(self):
        subcategory_ids = []
        if self.category_id:
            self._cr.execute('SELECT df_maintenance_equipment_subcategory_id FROM category_subcategory_rel WHERE maintenance_equipment_category_id = %s', (self.category_id.id,))
            records = self._cr.fetchall()
            for row in records:
                subcategory_ids.append(row[0])
            domain = [('id', 'in', subcategory_ids)]
            return {'domain': {'subcategory_id': domain}}


class MaintenanceObjectProduct(models.Model):
    _name = "df.maintenance.object.product"
    _description = "Maintenance object products"

    product_id = fields.Many2one('product.product', string="Product", required=True)
    product_qty = fields.Float(string="Product Qty", required=True, default=1.0)
    uom_id = fields.Many2one('uom.uom', string="Product UOM", required=True)
    asset_id = fields.Many2one('maintenance.equipment', string="Maintenance object", ondelete='cascade', required=True)

    _sql_constraints = [('product_uniq', 'unique(asset_id, product_id)',
                         'The product of the maintenance object must be unique.')]

    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id:
            #product = self.env ['product.product'].browse([self.product_id.id])
            # self.uom_id = product.uom_id
            self.uom_id = self.product_id.uom_id


class ResourceAttribute(models.Model):
    _name = "df.resource.attribute"
    _description = "Resource attributes"

    name = fields.Char('Attribute', size=64, required=True)
    value = fields.Char('Value', size=64, required=True)
    asset_id = fields.Many2one('maintenance.equipment', 'Asset', ondelete='cascade', required=True)

    _sql_constraints = [('attribute_uniq','unique(asset_id, name)',
                         'The attribute of the asset must be unique.')]
