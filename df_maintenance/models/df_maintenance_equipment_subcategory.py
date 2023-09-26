from odoo import api, fields, models, _, tools
from odoo.exceptions import ValidationError

class MaintenanceSubcategory(models.Model):
    _name = 'df.maintenance.equipment.subcategory'
    _description = 'Maintenance Subcategory'

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, record.name + '/' + record.code))
        return result

    name = fields.Char('Name',  required=True)
    code = fields.Char('Code',  required=True)
    # category_id = fields.Many2one('maintenance.equipment.category', string='Category')

    def unlink(self):
        for record in self:
            self._cr.execute('SELECT * FROM category_subcategory_rel WHERE df_maintenance_equipment_subcategory_id = %s', (record.id,))
            records = self._cr.fetchall()
            if len(records) >0:
                raise ValidationError(_("You cannot delete a subcategory that is already in use."))
        return super(MaintenanceSubcategory, self).unlink()


