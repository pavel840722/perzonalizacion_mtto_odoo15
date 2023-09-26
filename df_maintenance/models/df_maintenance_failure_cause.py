# -*- coding: utf-8 -*-

from odoo import api, fields, models, _, tools

class MaintenanceFailurType(models.Model):
    _name = 'df.maintenance.failure.type'
    _description = 'Failure types'

    name = fields.Char(size=64, required=True)
    asset_category_id = fields.Many2one('asset.category', string="Object category", required=True, readonly=True,
                                        ondelete='cascade')
    # company_id = fields.Many2one('res.company', string="Company",  readonly=True, required=True,
    #                              default=lambda self: self.env['res.company']._company_default_get('df.maintenance.failure.type',))



class MaintenanceFailureCause(models.Model):
    _name = 'df.maintenance.failure.cause'
    _description = 'Failure causes'

    name = fields.Char(size=64, required=True, index=True)
    # company_id = fields.Many2one('res.company', 'Company', required=True,
    #                              default=lambda self: self.env['res.company']._company_default_get('df.maintenance.failure.cause',))

    _sql_constraints = [
        ('name_failure_cause_uniq', 'unique(name)',
         'The name of the failure cause must be unique.'),
    ]

