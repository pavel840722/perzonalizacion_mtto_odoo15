from odoo import models, fields, api

class MaintenanceSearch(models.TransientModel):
    _name = 'df.maintenance.search.work.order'
    _description = "Search Work Order"

    request_id = fields.Many2one('maintenance.request', string='Maintenance Request', domain="[('stage_id', '!=', 1 ), ('create_uid', '=', uid)]")
    work_order_ids = fields.Many2many('df.maintenance.work.order', string='Work Order', create=False, readonly=True)
    activities_ids = fields.One2many('df.maintenance.search.extra.activy','search', readonly=True)
    product_ids = fields.One2many('df.maintenance.search.extra.product','search', readonly=True)
    employee_ids = fields.One2many('df.maintenance.search.extra.employe','search', readonly=True)
    costo_total = fields.Float('Total cost', compute="_compute_costo_total")
    costo_materiales = fields.Float('Materials cost', compute="_compute_costo_materiales")
    costo_mano_obra = fields.Float('Jobs cost', compute="_compute_costo_mano_obra")


    @api.depends('request_id')
    def _compute_costo_total(self):
        wo_list_active = self.env['df.maintenance.work.order'].search([('request_id', '=', self.request_id.id)])
        monto_total = 0
        for order in wo_list_active:
            monto_total = monto_total + order.total_amount
        self.costo_total = monto_total

    @api.depends('request_id')
    def _compute_costo_materiales(self):
        wo_list_active = self.env['df.maintenance.work.order'].search([('request_id', '=', self.request_id.id)])
        monto_total = 0
        for order in wo_list_active:
            monto_total = monto_total + order.product_amount
        self.costo_materiales = monto_total

    @api.depends('request_id')
    def _compute_costo_mano_obra(self):
        wo_list_active = self.env['df.maintenance.work.order'].search([('request_id', '=', self.request_id.id)])
        monto_total = 0
        for order in wo_list_active:
            monto_total = monto_total + order.labor_amount
        self.costo_mano_obra = monto_total


    def action_search(self):
        pass

    @api.onchange('request_id')
    def _onchange_request_id(self):
        if self.request_id:
            wo_list_active = self.env['df.maintenance.work.order'].search([('request_id','=',self.request_id.id)])
            self.activities_ids = False
            self.product_ids = False
            self.employee_ids = False
            list = []
            list_actividades = []
            list_product = []
            list_job = []
            for ids_w in wo_list_active:
                list.append(ids_w.id)
                for actividades in ids_w.activity_ids:
                    vals_aux = (0, 0, {'activities_id': actividades.activity.id})
                    list_actividades.append(vals_aux)

                    # cont = 0
                    # if list_actividades:
                    #     for activity_id in list_actividades:
                    #         if actividades.activity.id == activity_id[2]['activities_id']:
                    #             cont = activity_id[2]['cant'] + 1
                    #             activity_id[2]['cant'] = cont
                    #         else:
                    #             cont_3 = 0
                    #             for aux_activity in list_actividades:
                    #                 if actividades.activity.id != aux_activity[2]['activities_id']:
                    #                     cont_3 = cont_3 + 1
                    #             if cont_3 == len(list_actividades):
                    #                 vals_aux = (0, 0, {'activities_id': actividades.activity.id,
                    #                                         'cant': 1})
                    #                 if vals_aux:
                    #                     list_product.list_actividades(vals_aux)
                    #                     break
                    # else:
                    #     vals_aux = (0, 0, {'activities_id': actividades.activity.id,
                    #                        'cant': cont})
                    #     list_actividades.append(vals_aux)

                for product in ids_w.product_ids:
                    cont = 0
                    if list_product:
                        for product_id in list_product:
                            if product.product_id.id == product_id[2]['product_id']:
                                cont = product_id[2]['cant'] + 1
                                product_id[2]['cant'] = cont
                            else:
                                cont_3 = 0
                                for aux_product in list_product:
                                    if product.product_id.id != aux_product [2]['product_id']:
                                        cont_3 = cont_3 + 1
                                if cont_3 == len(list_product):
                                    vals_aux = (0, 0, {'product_id': product.product_id.id,
                                                            'cant': 1})
                                    if vals_aux:
                                        list_product.append(vals_aux)
                                        break
                    else:
                        vals_aux = (0, 0, {'product_id': product.product_id.id,
                                               'cant':1})
                        list_product.append(vals_aux)

                for job in ids_w.employee_ids:
                    cont = 0
                    if list_job:
                         for job_id in list_job:
                            if job.job_id.id == job_id[2]['job_id']:
                                cont = job_id[2]['cant'] + 1
                                job_id[2]['cant'] = cont
                            else:
                                cont_3 = 0
                                for aux_job in list_job:
                                    if job.job_id.id != aux_job[2]['job_id']:
                                        cont_3 = cont_3 + 1
                                if cont_3 == len(list_job):
                                    vals_aux = (0, 0, {'job_id': job.job_id.id,
                                                       'cant': 1})
                                    if vals_aux:
                                        list_job.append(vals_aux)
                                        break
                    else:
                        vals_aux = (0, 0, {'job_id': job.job_id.id,
                                           'cant': 1})
                        list_job.append(vals_aux)

            self.write({'work_order_ids': [(6, 0, list)]})
            self.activities_ids = list_actividades
            self.product_ids = list_product
            self.employee_ids = list_job











class MaintenanceSearchExtraActivy(models.TransientModel):
    _name = 'df.maintenance.search.extra.activy'

    search = fields.Many2one('df.maintenance.search.work.order')
    activities_id = fields.Many2one('df.maintenance.activity', string='Activities', create=False)
    costo_total = fields.Float(string='Amount',compute="_compute_costo_total")

    @api.depends('search')
    def _compute_costo_total(self):
        wo_list_active = self.env['df.maintenance.work.order'].search([('request_id', '=', self.search.request_id.id)])
        for record in self:
            monto_total = 0
            for order in wo_list_active:
                for activity in order.activity_ids:
                    amount_job = 0
                    amount_product = 0
                    if activity.activity.id == record.activities_id.id:
                        for job in wo_list_active.employee_ids:
                            if job.activity_id.id == activity.activity.id:
                                amount_job = amount_job + job.amount
                        for product in wo_list_active.product_ids:
                            if product.activity_id.id == activity.activity.id:
                                amount_product = amount_product + product.amount
                        monto_total = amount_product + amount_job
                    record.costo_total = monto_total






class MaintenanceSearchExtraProduct(models.TransientModel):
    _name = 'df.maintenance.search.extra.product'

    search = fields.Many2one('df.maintenance.search.work.order')
    product_id = fields.Many2one('product.product', string='Product', create=False)
    cant = fields.Float(string='Quanty')



class MaintenanceSearchExtraEmployee(models.TransientModel):
    _name = 'df.maintenance.search.extra.employe'

    search = fields.Many2one('df.maintenance.search.work.order')
    job_id = fields.Many2one('hr.job', string='Job', create=False)
    cant = fields.Float(string='Quanty')

