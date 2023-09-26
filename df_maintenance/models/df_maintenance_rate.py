from odoo import api, fields, models, _, tools


class MaintenanceRate(models.Model):
    _name = 'df.maintenance.rate'
    _description = 'Maintenance Rate'
    _rec_name = 'id'

    brigade_id = fields.Many2one('df.maintenance.brigade', 'Brigade Reference',required = True)
    department_id = fields.Many2one('hr.department',required = True)
    job_id = fields.Many2one('hr.job', 'Job',domain="[('department_id', '=', department_id )]",required = True)
    hourly_rate = fields.Float('Hourly Rate')

    @api.onchange('brigade_id')
    def _onchange_department(self):
        self.department_id = self.brigade_id.hr_department


    @api.onchange('brigade_id')
    def _onchange_job_id(self):
        self.job_id = False



    _sql_constraints = [
        ('position_uniq', 'unique(job_id,brigade_id)', _('The position must be unique.'))]

    # @api.model
    # def create(self, vals):
    #     vals['sequence'] = self.env['ir.sequence'].get('df.maintenance.rate')
    #     return super(MaintenanceRate, self).create(vals)

