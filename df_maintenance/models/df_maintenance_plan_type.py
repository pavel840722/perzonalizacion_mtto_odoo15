# -*- coding: utf-8 -*-

from odoo import api, fields, models, _, tools
from odoo.exceptions import UserError, ValidationError
import re

class MaintenanceEquipmentCategory(models.Model):
    _inherit = 'maintenance.equipment.category'

    plan_type_id = fields.Many2one('df.maintenance.plan.type', string='Plan type')



class MaintenancePlanType(models.Model):
    """Defines a plan type that groups several resource categories."""

    _name = 'df.maintenance.plan.type'
    _description = 'Maintenance Plan Types'

    name = fields.Char(size=64, required=True, index=True)
    asset_category_ids = fields.One2many('maintenance.equipment.category',
                                          'plan_type_id', 'Maintenance Asset Categories')
    company_id = fields.Many2one('res.company', 'Company', required=True,
                                 default=lambda self: self.env['res.company']._company_default_get(
                                     'df.maintenance.plan.type',
                                 ))

    _sql_constraints = [
        ('name_plan_type_uniq', 'unique(name)',
         '''The name of the plan type must be unique.'''),
    ]

    @api.model
    def create(self, vals):
        if not re.match("^[a-zA-ZñáéíóúüÑÁÉÍÓÚÜ\\ \\d]+$", vals.get('name')):
            raise ValidationError(_("You cannot enter strange characters in the name field."))
        return super(MaintenancePlanType, self).create(vals)

    def write(self, vals):
        if vals.get('name'):
            if not re.match("^[a-zA-ZñáéíóúüÑÁÉÍÓÚÜ\\ \\d]+$", vals.get('name')):
                raise ValidationError(_("You cannot enter strange characters in the name field."))
        return super(MaintenancePlanType, self).write(vals)


