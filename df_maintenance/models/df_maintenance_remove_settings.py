from odoo import api, fields, models, _, tools
from odoo.exceptions import UserError, ValidationError

class MaintenanceRemoveSettings(models.Model):
    _name = 'df.maintenance.remove.settings'
    _description = 'Maintenance Remove Settings'

    name = fields.Char(default='Remove Settings')
    days_to_remove_order = fields.Integer('Days to remove order')
    free_state_materials_remove = fields.Integer('Days to remove materials in free state')

    # @api.model_create_multi
    # def create(self, vals_list):
    #     records = self.search([]).ids
    #     if len(records) == 0:
    #         return super(MaintenanceRemoveSettings, self).create(vals_list)
    #     else:
    #         raise ValidationError(_("A delete configuration already exists."))





