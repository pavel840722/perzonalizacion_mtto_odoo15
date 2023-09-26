from odoo import api, fields, models, _, tools

class ProductTemplate(models.Model):
    _inherit = "product.template"

    _sql_constraints = [
        ('name_uniq', 'unique(name)', _('The product name must be unique.'))]
