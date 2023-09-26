from odoo import api, fields, models, _, tools

class MaintenanceRequestArea(models.Model):

    _name = 'df.maintenance.request.area'
    _description = 'Maintenance Request Area'

    # @api.model
    # def _get_selected_areas(self):
    #     areas = []
    #     for request_area in self.request_id.request_areas:
    #         areas.append(request_area.area_id)
    #     res = [('id', 'not in', areas)]
    #
    #     return res

    area_id = fields.Many2one('maintenance.team', 'Area', required=True) # domain=lambda self: self._get_selected_areas()
    brigades_ids = fields.Many2many('df.maintenance.brigade', 'df_request_area_brigade', 'request_area_id', 'brigade_id', required=True)
    request_id = fields.Many2one('maintenance.request', 'Area', required=True, ondelete='cascade')

    _sql_constraints = [
        ('are_request_uniq', 'unique(area_id,request_id)', _('The area must be unique by request.'))]

    @api.onchange('area_id')
    def onchange_area_id(self):
         if self.area_id:
            self.brigades_ids = False
            brigadas_ids = self.env['df.maintenance.brigade'].search([('id', 'in' , tuple(self.area_id.brigades.ids))]).ids
            domain_brigadas = [('id', 'in', brigadas_ids)]
            # areas_ids = self.env['maintenance.team'].search([('id','!=', self.area_id.id)])
            # domain_areas = [('id','in', areas_ids)]
            return {'domain': {'brigades_ids': domain_brigadas}}





