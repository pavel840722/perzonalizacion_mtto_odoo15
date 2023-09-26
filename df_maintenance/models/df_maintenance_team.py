from odoo import api, fields, models, _, tools
from lxml import etree
import json
from odoo.exceptions import ValidationError

class MaintenanceTeam(models.Model):
    _inherit = 'maintenance.team'

    @api.model
    def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):
        context = self._context
        res = super(MaintenanceTeam, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                              submenu=submenu)
        if view_type == 'tree':
            doc = etree.XML(res['arch'])
            for node in doc.xpath("//field[@name='member_ids']"):
                node.set('invisible', '1')
                modifiers = json.loads(node.get('modifiers', '{}'))
                modifiers['tree_invisible'] = True
                modifiers['column_invisible'] = True
                node.set('modifiers', json.dumps(modifiers))
            res['arch'] = etree.tostring(doc)
        return res

    serie = fields.Integer(string='Serie')
    brigades = fields.One2many('df.maintenance.brigade', 'team_id', string='Brigades')
    # analytic_account = fields.Many2one('account.analytic.account', 'Analytic Account', required=True)
    # hr_deparment = fields.Many2one('hr.department', 'HR Deparment', require=True)

    _sql_constraints = [('name_uniq', 'unique(name)', _('The name must be unique.'))]

    @api.onchange('brigades')
    def _onchange_brigades(self):
            for brigade in self.brigades:
                number = brigade.number
                digitos = []
                while number > 0:
                    digito = number % 10
                    digitos.append(digito)
                    number = number // 10
                digitos.reverse()
                digito_real = []
                cont = 0
                for num in digitos:
                    digito_real.append(num)
                    cont = cont + 1
                    if cont == 2:
                        break
                brigade_number = int(''.join(map(str, digito_real)))
                if self.serie != brigade_number:
                    raise ValidationError(_("The brigade don not belong this Maintenance Area."))

    @api.model
    def create(self, vals):
        areas = self.search([])
        for area in areas:
            for brigada in area.brigades:
                if brigada.id in vals['brigades'][0][2]:
                    raise ValidationError(_('A brigade can only be assigned to one maintenance area.'))
        return super(MaintenanceTeam, self).create(vals)

    def write(self, vals):
        if vals.get('brigades'):
            areas = self.search([('id','!=',self.id)])
            for area in areas:
                for brigada in area.brigades:
                    if vals['brigades'][0][2]:
                        if brigada.id in vals['brigades'][0][2]:
                            raise ValidationError(_('A brigade can only be assigned to one maintenance area.'))

        return super(MaintenanceTeam, self).write(vals)

    def unlink(self):
        for record in self:
            request_area_objs = self.env['df.maintenance.request.area'].search([('area_id','=',record.id)])
            if len(request_area_objs) > 0:
                raise ValidationError(_('The operation cannot be completed: the record being deleted is needed by another model. If possible, file it instead.'))
        super(MaintenanceTeam, self).unlink()



# class HrDepartment(models.Model):
#     _inherit = 'hr.department'
#
#     def name_get(self):
#         res = []
#         for department in self:
#             name = department.code
#             res.append((department.id, name))
#         return res

    # analytic_account = fields.Many2one('account.analytic.account', 'Analytic Account', groups="df_maintenance.group_maintenance_administrator")
    #
