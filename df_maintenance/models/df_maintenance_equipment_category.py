# -*- coding: utf-8 -*-

from odoo import api, fields, models, _, tools
from lxml import etree
import json

class MaintenanceEquipmentCategory(models.Model):
    _inherit = 'maintenance.equipment.category'

    @api.model
    def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):
        context = self._context
        res = super(MaintenanceEquipmentCategory, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                           submenu=submenu)
        if view_type == 'tree':
            doc = etree.XML(res['arch'])
            for node in doc.xpath("//field[@name='technician_user_id']"):
                node.set('invisible', '1')
                modifiers = json.loads(node.get('modifiers', '{}'))
                modifiers['tree_invisible'] = True
                modifiers['column_invisible'] = True
                node.set('modifiers', json.dumps(modifiers))
            res['arch'] = etree.tostring(doc)
        return res

    subcategories_ids = fields.Many2many('df.maintenance.equipment.subcategory', 'category_subcategory_rel',  string='Subcategories')
