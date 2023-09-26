from odoo import api, fields, models, _, tools
from odoo.exceptions import ValidationError

class PhysicalLocation(models.Model):
    _name = 'df.maintenance.physical.location'
    _description = 'Physical location'

    name = fields.Char('Name', required=True)
    code = fields.Char('Code', required=True)
    analytic_account = fields.Many2one('account.analytic.account', 'Analytic Account', required=True)

    def unlink(self):
        for record in self:
            self._cr.execute('SELECT * FROM maintenance_equipment WHERE stock_asset_id = %s', (record.id,))
            records = self._cr.fetchall()
            if len(records) > 0:
                raise ValidationError(
                    _('The operation cannot be completed: the record being deleted is needed by another model. If possible, file it instead.'))
        super(PhysicalLocation, self).unlink()


_sql_constraints = [
    ('name_uniq', 'unique(name)',  'The name must be unique.'),
    ('name_code', 'unique(code)',  'The code must be unique.'),
]
