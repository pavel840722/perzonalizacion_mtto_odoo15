from odoo import api, fields, models, _, tools
from odoo.osv import expression
from odoo.exceptions import ValidationError

class DepartmentCentroCosto(models.Model):

    _name = 'df.maintenance.department.centro'

    department = fields.Many2many('hr.department', string='Department',required=True)
    cost_center = fields.Many2one('account.analytic.account', 'Analytic Account',
                                  domain="[('id', 'in', cost_center_allowed )]", required=True)
    cost_center_allowed = fields.Many2many('account.analytic.account', 'Analytic Account',
                                           compute='_compute_cost_center_allowed')


    @api.depends('cost_center')
    def _compute_cost_center_allowed(self):
        for record in self:
            list = []
            center = self.env['account.analytic.account'].search([('code', 'in', ('202', '207', '203', '206', '214', '212'))])
            for index in center:
                list.append(index.id)
            record.cost_center_allowed = list


    _sql_constraints = [
        ('cost_center_uniq', 'unique (cost_center)', 'The cost center must be unique per company !')
    ]