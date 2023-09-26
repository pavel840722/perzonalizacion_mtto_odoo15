from odoo import api, fields, models, _, tools
from odoo.exceptions import ValidationError

class MaintenanceBrigade(models.Model):

    _name = 'df.maintenance.brigade'
    _description = 'Brigade'
    _rec_name = 'hr_department'


    number = fields.Integer(string="Number", required=True)
    team_id = fields.Many2one('maintenance.team', string='Area')
    activity_ids = fields.Many2many('df.maintenance.activity',string ='Activities',compute='_compute_activity_ids')
    hr_department = fields.Many2one('hr.department', 'HR Department', require=True)
    vacio = fields.Boolean('ES vacio',compute='_compute_vacio')
    analytic_account = fields.Many2one('account.analytic.account', 'Analytic Account', required=True)


    def _compute_vacio(self):
        for record in self:
            if record.activity_ids:
                record.vacio = False
            else:
                record.vacio = True

    def _compute_activity_ids(self):
        for record in self:
            list=[]
            activities = self.env['df.maintenance.activity'].search([('brigade_id','=',record.id)])
            for activity in activities:
                list.append(activity.id)
            record.write({'activity_ids': [(6, 0, list)]})

    # @api.onchange('activity_ids')
    # def onchange_activity_ids(self):
    #     for aun in self:
    #         for record in aun.activity_ids:
    #             activitys = self.env['df.maintenance.activity'].search([])
    #             for activity in activitys:
    #                 if activity.id == record.activity_id.id:
    #                     activity.brigade_origin = aun.id

    def name_get(self):
        res = []
        for brigada in self:
            name = brigada.hr_department.name
            res.append((brigada.id, name))
        return res

    def unlink(self):
        for record in self:
            self._cr.execute('SELECT * FROM df_request_area_brigade WHERE brigade_id = %s', (record.id,))
            records = self._cr.fetchall()
            if len(records) > 0:
                raise ValidationError(_('The operation cannot be completed: the record being deleted is needed by another model. If possible, file it instead.'))
        super(MaintenanceBrigade, self).unlink()



# class MaintenanceBrigadeActivity(models.Model):
#
#     _name = 'df.maintenance.brigade.activity'
#     _rec_name = "brigade_id"
#
#     brigade_id = fields.Many2one('df.maintenance.brigade' ,'Brigade' , required=True, ondelete='cascade')
#     activity_id = fields.Many2one('df.maintenance.activity', string='Activities',required=True)
#
#     _sql_constraints = [
#         ('activity_ids_uniq', 'unique(activity_id,brigade_id)', "You can't have same activity in the same brigade."),
#     ]



    # @api.onchange('activity_id')
    # def onchange_activity_id(self):
    #     all_activities = self.env['df.maintenance.brigade'].search([])
    #     for act in all_activities.activity_ids:
    #          if act.activity_id.name == self.activity_id.name:
    #              raise ValidationError(_("A activity can't belong to more one brigade."))

        # activity_obj = self.env['df.maintenance.activity'].search([])
        # for act in activity_obj:
        #     if act.name == self.activity_id.name:
        #         data = {
        #               'brigade': self.brigade_id
        #          }
        #         act.sudo().write(data)






