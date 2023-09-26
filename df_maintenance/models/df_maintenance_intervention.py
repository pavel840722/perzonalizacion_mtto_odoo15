# -*- coding: utf-8 -*-

from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, exceptions, tools
#import openerp.netsvc as netsvc
from odoo.tools.translate import _
from odoo.addons import decimal_precision as dp
from datetime import date, datetime
import pytz
from dateutil import rrule
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import UserError, ValidationError
import re

class MaintenancePreventiveIntervention(models.Model):
    """
    Defines a set of activities, products and jobs involved in maintenance.
    """
    _name = 'df.maintenance.intervention'
    _description = 'Maintenance intervention'
    # _parent_name = "inclusion_id"
    # _parent_store = True
    # _parent_order = 'abbreviation'

    @api.depends('inclusion_id', 'inclusion_id.inclusion_id')
    def _get_domain_includes(self):
        """
        Get all interventions includes by the intervention for use in a domain
        in field domain_includes.

        :rtype: string
        :return: Returns the interventions ids in a string format
        """
        intervention_ids = []
        if self:
            intervention_ids = self._get_includes_by_id(True, True)
        if len(intervention_ids) > 0: #Esto lo puse, Pavel
            self.domain_includes = intervention_ids[0].ids


    name = fields.Char(size=64, required=True)
    internal_working_budget = fields.Float(compute='_compute_total_budget', digits=dp.get_precision('Account'))
    abbreviation = fields.Char(size=64, required=True)
    duration = fields.Float(required=True)
    downtime = fields.Float(default=0)
    inclusion_id = fields.Many2one('df.maintenance.intervention', 'Inclusion', ondelete='set null')
    parent_left = fields.Integer(string="Left Parent")
    parent_right = fields.Integer(string="Right Parent")
    activity_ids = fields.Many2one('df.maintenance.activity', 'Activities')
    product_ids = fields.One2many('df.maintenance.intervention.product', 'intervention_id', 'Products')
    job_ids = fields.One2many('df.maintenance.intervention.job', 'intervention_id', 'Jobs')
    template_ids = fields.One2many('df.maintenance.intervention.template',
                                   'intervention_id', 'Templates')
    domain_includes = fields.Many2many('df.maintenance.intervention', 'df_maintenance_intervention_include',
                                       'intervention_id', 'intervention_include_id', compute='_get_domain_includes',
                                       store=True)
    company_id = fields.Many2one('res.company', 'Company', required=True,
                                 default=lambda self: self.env['res.company']._company_default_get(
                                     'df.maintenance.template',
                                 ))
    total_job_amount = fields.Float(compute='_job_amount', digits=(10, 2))

    is_subcontracted = fields.Boolean('Is Subcontracted', default=False)
    partner_id = fields.Many2one('res.partner', 'Partner', default=None)
    budget = fields.Float('Maintenance Cost', digits=dp.get_precision('Account'), default=0)
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  default=lambda self: self.env.user.company_id.currency_id)

    @api.depends('job_ids')
    def _job_amount(self):
        for intervention in self:
            sum_amount = 0.0
            for job in intervention.job_ids:
                sum_amount = sum_amount + job.amount
            intervention.total_job_amount = sum_amount

    @api.depends('job_ids', 'product_ids')
    def _compute_total_budget(self):
        for intervention in self:
            sum_amount = 0.0
            for job in intervention.job_ids:
                sum_amount = sum_amount + job.amount
            for product in intervention.product_ids:
                sum_amount = sum_amount + product.amount

            intervention.internal_working_budget = sum_amount

    _sql_constraints = [
        ('downtime', 'CHECK (downtime >= 0)', 'Downtime must be >= 0.'),
        ('duration', 'CHECK (duration > 0)', 'Duration must be > 0.')]

    _sql_uniques = [
        ('name_unique', '(company_id, upper(name))', 'Intervention\'s name must be unique.')]

    @api.model
    def create(self, vals):
        if 'activity_ids' not in vals or len(vals['activity_ids']) < 1:
            raise ValidationError(_("Maintenance intervention must associate at least one activity."))
            # raise exceptions.Warning(_('''Maintenance intervention must associate at least one activity.'''))
        if vals['is_subcontracted']:
            vals['product_ids'] = [(6, False, [])]
            vals['job_ids'] = [(6, False, [])]
        return super(MaintenancePreventiveIntervention, self).create(vals)


    def write(self, vals):
        if (('activity_ids' in vals and len(vals['activity_ids']) < 1) or not self._check_for_activities()):
            raise ValidationError(_("Error occurred while validating the field(s)"), _('''Maintenance intervention must associate at least one activity.'''))
            # raise exceptions.Warning(_("Error occurred while validating the field(s)"), _('''Maintenance intervention must associate at least one activity.'''))
        if vals.get('is_subcontracted', False):
            if vals['is_subcontracted']:
                self.product_ids.unlink()
                self.job_ids.unlink()
                vals['product_ids'] = [(6, False, [])]
                vals['job_ids'] = [(6, False, [])]
            else:
                vals['partner_id'] = False
                vals['budget'] = False
        return super(MaintenancePreventiveIntervention, self).write(vals)


    def _get_includes_by_parent_left_right(self, parent_left, parent_right, inclusive, parent):
        """
        Get all interventions includes by the intervention in self searching in
        right and left parents.

        :param list parent_left: list of ids of the left parents
        :param list parent_right: list of ids of the right parents
        :param boolean inclusive: a boolean if the intervention is included itself
        :param boolean parent: a boolean if the included list of intervention is returned
        :rtype: list
        :return: Returns the interventions ids
        """
        self.ensure_one()
        signal = ['>', '<']
        if inclusive:
            signal = ['>=', '<=']

        intervention_ids = {}
        intervention_ids = self.search([('parent_left', signal[parent], parent_left), \
                                        ('parent_right', signal[not parent], parent_right)], \
                                       order='parent_left')
        return intervention_ids

    def _get_includes_by_id(self, inclusive, parent):
        """
        Get all interventions includes by the intervention in self.

        :param boolean inclusive: True if the intervention is included itself
        :param boolean parent: True if the included list of intervention is returned
        :rtype: list
        :return: Returns the interventions ids
        """

        return self._get_includes_by_parent_left_right(self.parent_left, self.parent_right, inclusive, parent)

    def _check_for_activities(self):
        """
        Returns a list of ids of intervention activities associated maintenance
        at least one Maintenance Intervention.
        :rtype: list
        """
        act_count = self.env['df.maintenance.intervention.activity'].search_count([('intervention_id', '=', self.id)])
        return act_count


    def _check_for_jobs(self):
        """
        Returns list of ids of intervention job associated maintenance at least
        one Maintenance Intervention.
        :rtype: list
        """
        job_count = self.env['df.maintenance.intervention.job'].search_count([('intervention_id', '=', self.id)])
        return job_count

    _constraints = [(models.Model._check_recursion, 'You can not include recursive Interventions.', ['inclusion_id']),
                    (_check_for_activities, 'Maintenance intervention must associate at least one activity.', ['activity_ids']),
                   ]


# class MaintenancePreventiveInterventionActivity(models.Model):
#     """
#     Defines the activities of the maintenance interventions.
#     """
#     _name = 'df.maintenance.intervention.activity'
#     _description = 'Intervention activities'
#
#     # name = fields.Char(string="Description", size=255, required=True)
#     activity = fields.Many2one('df.maintenance.activity', 'Activity', required=True)
#     sequence = fields.Integer(required=True)
#     intervention_id = fields.Many2one('df.maintenance.intervention', 'Intervention')
#
#     _sql_constraints = [
#         ('sequence', 'CHECK (sequence > 0)', 'Sequence must be > 0.'),
#         ('activity_uniq', 'unique(intervention_id, name, sequence)',
#          'The sequence and name combination of values must be unique in a intervention.')]


class MaintenancePreventiveInterventionProduct(models.Model):
    """
    Defines the product and unit of measure of the maintenance interventions.
    """
    _name = 'df.maintenance.intervention.product'
    _description = 'Intervention products'

    quantity = fields.Float('Quantity Req', required=True, default=0.0)
    product_id = fields.Many2one('product.product', 'Product', required=True)
    intervention_id = fields.Many2one('df.maintenance.intervention', 'Intervention')
    uom_id = fields.Many2one('uom.uom', 'UDM', required=True, related='product_id.uom_id')
    price_unit = fields.Float('Precio Unitario', digits=(10, 2), readonly=True, related='product_id.standard_price')
    amount = fields.Float(compute='_compute_total', string='Importe', digits=(10, 2), readonly=True, )


    @api.depends('quantity', 'price_unit')
    def _compute_total(self):
        for product in self:
            product.amount = product.quantity * product.price_unit

    _sql_constraints = [
        ('product_uniq', 'unique(intervention_id, product_id)', 'Product must be unique in a intervention.'),
        ('quantity', 'CHECK (quantity > 0)', 'Wrong product quantity value in model, they must be positive.')
    ]


class MaintenancePreventiveInterventionJob(models.Model):
    """
    Defines the job of Maintenance Intervention.
    """
    _name = 'df.maintenance.intervention.job'
    _description = 'Intervention employees'

    time = fields.Float(required=True)
    job_id = fields.Many2one('hr.job', 'Job viejo', required=False)
    position_id = fields.Many2one('l10n_cu_hr.position', 'Job', required=True)
    intervention_id = fields.Many2one('df.maintenance.intervention', 'Intervention')
    employee_id = fields.Many2one('hr.employee', 'Employee', required=False)
    amount = fields.Float('Amount', digits=(10, 2), required=True)

    @api.onchange('position_id', 'time')
    def _onchange_amount(self):
        self.amount = self.position_id.salary / 192 * self.time

    _sql_constraints = [
        ('job_uniq', 'unique(intervention_id, job_id)', 'Job must be unique in a intervention.')
    ]


class MaintenancePreventiveTemplate(models.Model):
    """
    Defines a set of interventions that have a particular regime.
    """
    _name = 'df.maintenance.template'
    _description = 'Maintenance template'
    _inherit = ['mail.thread']


    @api.depends('intervention_ids.regimen')
    def _calc_regimen(self):
        calendar = [intervention_id.regimen == 'calendar' for intervention_id in self.intervention_ids]
        reading = [intervention_id.regimen == 'reading' for intervention_id in self.intervention_ids]
        if all(calendar):
            self.regimen = 'calendar'
        elif all(reading):
            self.regimen = 'reading'
        else:
            self.regimen = 'both'

    name = fields.Char(size=64, required=True)
    description = fields.Text()
    regimen = fields.Selection([('calendar', 'Calendar'), \
                                ('reading', 'Reading'), \
                                ('both', 'Calendar and Reading')], 'Regimen', \
                               readonly=True, compute=_calc_regimen, strore=True)
    state = fields.Selection([('draft', 'Draft'),
                              ('confirmed', 'Confirmed'),
                              ('expired', 'Expired')],
                             'State', required=True, readonly=True, default=lambda *a: 'draft',
                             track_visibility='onchange')

    intervention_ids = fields.One2many('df.maintenance.intervention.template', \
                                       'template_id', 'Interventions')
    company_id = fields.Many2one('res.company', 'Company', required=True,
                                 default=lambda self: self.env['res.company']._company_default_get(
                                     'df.maintenance.template',
                                 ))

    _sql_constraints = [
        ('name_uniq', 'unique(name)', _('The name must be unique.'))]

    @api.model
    def create(self, vals):
        if not re.match("^[a-zA-ZñáéíóúüÑÁÉÍÓÚÜ\\ \\d]+$", vals.get('name')):
            raise ValidationError(_("You cannot enter strange characters in the name field."))
        return super(MaintenancePreventiveTemplate, self).create(vals)

    def write(self, vals):
        if vals.get('name'):
            if not re.match("^[a-zA-ZñáéíóúüÑÁÉÍÓÚÜ\\ \\d]+$", vals.get('name')):
                raise ValidationError(_("You cannot enter strange characters in the name field."))
        return super(MaintenancePreventiveTemplate, self).write(vals)

    def _check_associated_object(self):
        """
        Returns True if maintenance objects (technical files) arn't associated
        with a Maintenance Template selected.
        :rtype: boolean
        """
        asset_count = self.env['asset.asset'].search_count([('maintenance_template_id', '=', self.id)])
        if asset_count != 0:
            raise ValidationError(_("Error occurred while validating the field(s)"), _("Can not change Template\'s status because is associated with a maintenance object."))
            # raise exceptions.Warning(_("Error occurred while validating the field(s)"), _("Can not change Template\'s status because is associated with a maintenance object."))
        return True

    def _check_associated_object_1(self):
        """
        Returns True if maintenance objects (technical files) arn't associated
        with a Maintenance Template selected.
        :rtype: boolean
        """
        self.ensure_one()
        asset_count = self.env['asset.asset'].search_count([('maintenance_template_id', '=', self.id)])
        if asset_count != 0:
            return False
        return True

    def _check_interventions(self):
        """
        Returns True if exist at least one intervention associated with a Maintenance Template selected.
        :rtype: boolean
        """
        intervention_count = self.env['df.maintenance.intervention.template'].search([('template_id', '=', self.id)])
        if intervention_count == 0:
            raise ValidationError(_("Error occurred while validating the field(s)"),
                                     _("Can not change Template\'s status because no have at least one intervention."))

            # raise exceptions.Warning(_("Error occurred while validating the field(s)"),
            #                          _("Can not change Template\'s status because no have at least one intervention."))
        return True

    @api.model
    def _msg_check_for_interventions(self):
        raise ValidationError(_('Error occurred while validating the field(s)'),
                                 _('This intervention is already associated with the Maintenance Template.'))

        # raise exceptions.Warning(_('Error occurred while validating the field(s)'),
        #                          _('This intervention is already associated with the Maintenance Template.'))


    def action_draft1(self):
        """
        Change Maintenance Template state to draft.
        """
        for template in self:
            if template.state == 'confirmed':
                template._check_associated_object()
            template.write({'state': 'draft'})
        return True


    def action_confirmed(self):
        """
        Change Maintenance Template state to confirmed.
        """
        for template in self:
            template._check_interventions()
            template.write({'state': 'confirmed'})
        return True


    def action_draft(self):
        for template in self:
            if template.state == 'confirmed':
                if template._check_associated_object_1():
                    template.write({'state': 'draft'})
                else:
                    wizard_obj = self.env['df.maintenance.caduce.template.wizard']
                    template_data = {
                        'draft': True,
                        'template_id': self.id
                    }
                    return {
                        'name': 'Confirme para cambiar estado',
                        'view_type': 'form',
                        'view_mode': 'form',
                        'res_model': 'df.maintenance.caduce.template.wizard',
                        'type': 'ir.actions.act_window',
                        'target': 'new',
                        'context': template_data
                    }
            else:
                template.write({'state': 'draft'})


    def action_expired(self):
        for template in self:
            if template.state == 'confirmed':
                if template._check_associated_object_1():
                    template.write({'state': 'expired'})
                else:
                    wizard_obj = self.env['df.maintenance.caduce.template.wizard']
                    template_data = {
                        'expired': True,
                        'template_id': self.id
                    }
                    return {
                        'name': 'Work Order Confirmation',
                        'view_type': 'form',
                        'view_mode': 'form',
                        'res_model': 'df.maintenance.caduce.template.wizard',
                        'type': 'ir.actions.act_window',
                        'target': 'new',
                        'context': template_data
                    }
            else:
                template.write({'state': 'expired'})

def str_to_date(string_date, format='%Y-%m-%d'):
    return datetime.strptime(string_date, format).date()


class MaintenancePreventiveInterventionTemplate(models.Model):
    """
    Defines the intervention of Maintenance Template.
    """
    _name = 'df.maintenance.intervention.template'
    _description = 'Maintenance Intervention Template'
    _rec_name = 'intervention_id'


    @api.depends('regimen', 'interval', 'rrule_type', 'uom_id', 'reading_frequency')
    def _calc_frequency(self):
        frequencies = ""
        if self.regimen == 'calendar' or self.regimen == 'both':
            frequencies += '%s %s' % (self.interval,
                                      self.rrule_type)

        if self.regimen == 'reading' or self.regimen == 'both':
            if self.regimen == 'both':
                frequencies += ' / '
            uom_name = self.uom_id.name
            frequencies += '%s %s' % (self.reading_frequency, uom_name)

        self.frequency = frequencies


    @api.depends('calendar', 'reading')
    def _calc_regimen(self):
        if self.calendar and self.reading:
            self.regimen = 'both'
        elif self.calendar:
            self.regimen = 'calendar'
        else:
            self.regimen = 'reading'

    regimen = fields.Selection([('calendar', 'Calendar'),
                                ('reading', 'Reading'),
                                ('both', 'Calendar and Reading')], 'Regimen',
                               required=True, compute='_calc_regimen')
    template_id = fields.Many2one('df.maintenance.template',
                                  'Template', required=True,
                                  ondelete='cascade')
    intervention_id = fields.Many2one('df.maintenance.intervention',
                                      'Intervention', required=True)

    calendar = fields.Boolean(string='Calendar')
    interval = fields.Integer('Repeat Every', help="Repeat every (Days/Week/Month/Year)", default=1)
    rrule_type = fields.Selection(
        [('daily', 'Day(s)'), ('weekly', 'Week(s)'), ('monthly', 'Month(s)'), ('yearly', 'Year(s)')], 'Recurrency',
        help="Let the event automatically repeat at that interval")
    mo = fields.Boolean('Mon')
    tu = fields.Boolean('Tue')
    we = fields.Boolean('Wed')
    th = fields.Boolean('Thu')
    fr = fields.Boolean('Fri')
    sa = fields.Boolean('Sat')
    su = fields.Boolean('Sun')
    month_by = fields.Selection([('date', 'Date of month'), ('day', 'Day of month')], 'Option', oldname='select1')
    day = fields.Integer('Date of month')
    week_list = fields.Selection([('MO', 'Monday'), ('TU', 'Tuesday'), ('WE', 'Wednesday'), ('TH', 'Thursday'),
                                  ('FR', 'Friday'), ('SA', 'Saturday'), ('SU', 'Sunday')], 'Weekday')
    byday = fields.Selection(
        [('1', 'First'), ('2', 'Second'), ('3', 'Third'), ('4', 'Fourth'), ('5', 'Fifth'), ('-1', 'Last')], 'By day')
    # READING FIELD
    reading = fields.Boolean(string='Reading')
    reading_frequency = fields.Integer(string="Reading Frequency",default=1)
    uom_id = fields.Many2one('uom.uom', 'Meter UOM') #Cambie, Pavel
    # Frecuency
    frequency = fields.Char(compute='_calc_frequency')



    @api.model
    def _prepare_reading_vals(self, intervention_template_id, schedule_id, until_date):

        result = dict(name=intervention_template_id.intervention_id.name,
                      count=not until_date and 2 or 1,
                      start=schedule_id.date_initial_schedule,
                      stop=schedule_id.date_initial_schedule,
                      end_type=until_date and 'end_date' or 'count',
                      final_date=until_date,
                      interval=schedule_id.reading_frequency_day,
                      month_by=False,
                      byday=False,
                      week_list=False,
                      recurrency=True,
                      recurrent_id=0,
                      rrule_type='daily',
                      show_as='busy',
                      allday=True,
                      )
        return result

    @api.model
    def _get_next_excecution_date(self, intervention_template_id, date_initial_schedule, until_date=False,
                                  reading_vals=None):
        """if param until_date is False return next_excecution_date else return list of next_excecution_date
        until_date :param for plan
        """

        calendar_env = self.env['calendar.event']
        calendar_vals = dict(name=intervention_template_id.intervention_id.name,
                             count=not until_date and 2 or 1,
                                start=date_initial_schedule,
                                stop=date_initial_schedule,
                             end_type=until_date and 'end_date' or 'count',
                             final_date=until_date,
                             interval=intervention_template_id.interval,
                             month_by=intervention_template_id.month_by,
                             partner_ids=[[6, False, [self.env.user.id]]],
                             byday=intervention_template_id.byday,
                             day=intervention_template_id.day,
                             mo=intervention_template_id.mo,
                             sa=intervention_template_id.sa,
                             su=intervention_template_id.su,
                             th=intervention_template_id.th,
                             tu=intervention_template_id.tu,
                             we=intervention_template_id.we,
                             week_list=intervention_template_id.week_list,
                             recurrency=True,
                             recurrent_id=0,
                             rrule_type=intervention_template_id.rrule_type,
                             show_as='busy',
                             allday=True,
                             )
        calendar = calendar_env.create(calendar_vals)
        rule = calendar.rrule

        startdate = pytz.UTC.localize(datetime.strptime(date_initial_schedule, DEFAULT_SERVER_DATE_FORMAT))
        rset1 = set()
        if rule:
            rset1 = rrule.rrulestr(str(rule), dtstart=startdate, forceset=True)

        dates = [d.astimezone(pytz.UTC) for d in rset1]
        dates = dates[1:]
        if dates and not until_date:
            return dates[0].strftime(DEFAULT_SERVER_DATE_FORMAT)
        if reading_vals:
            calendar2 = calendar_env.create(reading_vals)
            rule2 = calendar2.rrule
            rset2 = rrule.rrulestr(str(rule2), dtstart=startdate, forceset=True)
            reading_dates = [d.astimezone(pytz.UTC) for d in rset2]
            reading_dates = reading_dates[1:]
            dates.extend(reading_dates)
            dates = list(set(dates))  # remove duplicate date
            dates.sort()
        return dates

    _sql_constraints = [
        ('intervention_uniq',
         'unique(template_id, intervention_id)',
         'Intervention must be unique in a Template.')]