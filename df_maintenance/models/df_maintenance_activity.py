from odoo import api, fields, models, _, tools
from odoo.osv import expression
from odoo.exceptions import ValidationError

class MaintenanceActivity(models.Model):

    _name = 'df.maintenance.activity'
    _description = 'Maintenance Activity'


    name = fields.Char(size=64, required=True)
    intervention_ids = fields.One2many('df.maintenance.intervention','activity_ids','Intervention')
    product_ids = fields.One2many('df.maintenance.activity.product', 'activity_ids', 'Products')
    job_ids = fields.One2many('df.maintenance.activity.job', 'activity_ids', 'Employees')
    brigade_id = fields.Many2one('df.maintenance.brigade','Brigade Reference', required=True)
    department_id = fields.Many2one('hr.department','Department Reference')

    # @api.depends('brigade_id')
    # def _compute_department_id(self):
    #     for record in self:
    #         record.department_id = record.brigade_id.hr_department.id


    @api.onchange('brigade_id')
    def onchange_brigade_id(self):
        for record in self:
            record.department_id = record.brigade_id.hr_department.id

    # @api.multi
    # @api.depends('brigade_id')
    # def _compute_brigade_id(self):
    #     brigades = self.env['df.maintenance.brigade'].search([])
    #     for record in self:
    #         for brigade in brigades:
    #             for activity in brigade.activity_ids:
    #                 if activity.activity_id.id == record.id:
    #                     record.brigade_id = brigade.hr_department.id
    #         if record.brigade_id == False:
    #             pass


    def unlink(self):
        for record in self:
            self._cr.execute('SELECT * FROM df_work_order_activity WHERE activity = %s', (record.id,))
            records = self._cr.fetchall()
            if len(records) > 0:
                raise ValidationError(_('The operation cannot be completed: the record being deleted is needed by another model. If possible, file it instead.'))
        super(MaintenanceActivity, self).unlink()

    # @api.model
    # def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
    #     """ Returns a list of tuples containing id, name, as internally it is called {def name_get}
    #         result format: {[(id, name), (id, name), ...]}
    #     """
    #     args = args or []
    #     if operator == 'ilike' and not (name or '').strip():
    #         domain = []
    #     else:
    #         connector = '&' if operator in expression.NEGATIVE_TERM_OPERATORS else '|'
    #         domain = [connector, ('description', operator, name), ('name', operator, name)]
    #     return self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)



class MaintenanceActivityProduct(models.Model):
    _name = 'df.maintenance.activity.product'
    _description = 'Maintenance Activity'

    @api.onchange('price_unit', 'product_qty')
    def _calc_amount(self):
        self.amount = self.price_unit * self.quantity

    activity_ids = fields.Many2one('df.maintenance.activity','Activity')
    product_id = fields.Many2one('product.product', 'Product', required=True)
    quantity = fields.Float('Quantity Req', required=True, default=0.0)
    price_unit = fields.Float('Precio Unitario', digits=(10, 2), readonly=True, related='product_id.standard_price')
    amount = fields.Float(compute='_compute_total', string='Importe', digits=(10, 2), readonly=True, )
    uom_id = fields.Many2one('uom.uom', 'UDM', required=True, related='product_id.uom_id')
    is_activity = fields.Boolean(default=True)


    @api.depends('quantity', 'price_unit')
    def _compute_total(self):
        for product in self:
            product.amount = product.quantity * product.price_unit



class MaintenancePreventiveActivityJob(models.Model):
    """
    Defines the job of Maintenance Intervention.
    """
    _name = 'df.maintenance.activity.job'
    _description = 'Intervention employees'

    # def set_default(self):
    #     brigades = self.env['df.maintenance.brigade'].search([])
    #     for record in self.activity_ids:
    #         for brigade in brigades:
    #             for activity in brigade.activity_ids:
    #                 if activity.activity_id.id == record.id:
    #                     record.brigade_id = brigade.hr_department.id
    #         if record.brigade_id == False:
    #             pass



    activity_ids = fields.Many2one('df.maintenance.activity', 'Activity',required=True)
    time = fields.Float(required=True)
    job_id = fields.Many2one('hr.job', 'Job', required=False,domain="[('department_id', '=', department_id )]")
    # position_id = fields.Many2one('l10n_cu_hr.position', 'Job', required=True)
    # employee_id = fields.Many2one('hr.employee', 'Employee', required=False)
    amount = fields.Float('Amount', digits=(10, 2), required=True, compute='_compute_amount')
    is_activity = fields.Boolean(default=True)
    cant_job = fields.Integer(default=1)
    department_id = fields.Many2one('hr.department','Brigade',compute='compute_department_id')
    # default = set_default

    def compute_department_id(self):
        for record in self:
            record.department_id = record.activity_ids.department_id

    @api.onchange('job_id')
    def _onchange_job_id(self):
        for record in self:
            record.department_id = record.activity_ids.department_id

    @api.onchange('cant_job')
    def _onchange_cant_job(self):
        if self.cant_job <= 0:
            raise ValidationError(_("You cant't make a jobs with 0 or less "))

    @api.depends('job_id', 'time','cant_job')
    def _compute_amount(self):
        for record in self:
            rate = self.env['df.maintenance.rate'].search([('job_id', '=', record.job_id.id),
                                                           ('department_id','=',record.department_id.id) ])
            record.amount = rate.hourly_rate * record.time * record.cant_job





    _sql_constraints = [
        ('job_uniq', 'unique(intervention_id, job_id)', 'Job must be unique in a intervention.')
    ]
