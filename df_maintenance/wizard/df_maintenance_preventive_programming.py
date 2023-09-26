# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.tools.translate import _
from odoo import exceptions
import time
from datetime import datetime, date


class MaintenanceInitializeScheduleWizard(models.TransientModel):
    _name = "df.maintenance.initialize.schedule"
    _description = "Object Template Association"

    date_initial_schedule = fields.Date(string="Initial Date Schedule", default=date.today())
    asset_template_ids = fields.One2many('df.maintenance.object.template','initialize_schedule_id', 'Initialize Schedules')
    asset_category_id = fields.Many2one('maintenance.equipment.category', 'Asset category', required=True, ondelete='cascade')
    template_id = fields.Many2one('df.maintenance.template', 'Template', required=True)

    @api.onchange('asset_category_id', 'template_id')
    def onchange_template_id(self):
        asset_env = self.env['maintenance.equipment']
        asset_ids = asset_env.search([('category_ids', '=', self.asset_category_id.id),
                                        ('maintenance_template_id', '=', False)])
        asset_template_ids = []
        if self.template_id and self.asset_category_id:
            for asset in asset_ids:
                asset_template_ids.append({
                    'asset_id': asset.id,
                    'template_id': self.template_id.id
                })

        self.asset_template_ids = asset_template_ids

    def initialize(self):
        context = dict(self._context or {})
        object_template_pool = self.env['df.maintenance.object.template']
        reading_pool = self.env['l10n_cu_maintenance_preventive.reading_record_wizard']
        for record_id in self.asset_template_ids:
            for reading_id in record_id.reading_record_wizard_ids:
                messages = []
                if reading_id.average_value <= 0:
                    messages.append(_('''- Average usage values must be bigger than zero.\n'''))
                if reading_id.last_reading_date:
                    if reading_id.last_reading_date > time.strftime('%Y-%m-%d'):
                        messages.append(_('''- The reading date must be equal to or less than today.\n'''))
                    if reading_id.reading_id:
                        if reading_id.last_reading_date != reading_id.reading_id.reading_date or reading_id.last_reading_value != reading_id.reading_id.reading_value:
                            if reading_id.reading_id.reading_date >= reading_id.last_reading_date:
                                reading_date = datetime.strptime(reading_id.reading_id.reading_date, '%Y-%m-%d').date()
                                lang = self._context and self._context.get('lang', False) or False
                                lang_pool = self.env['res.lang']
                                lang_id = lang_pool.search([('code', '=', lang)])
                                format = lang_pool.read(['date_format'])[0]['date_format']
                                messages.append(
                                    _("- The reading date should be bigger than the last reading date '[%s]'.\n" % (
                                        date.strftime(reading_date, format))))
                            if reading_id.reading_id.reading_value >= reading_id.last_reading_value:
                                messages.append(
                                    _("- The reading value should be bigger than the last reading value '[%s]'.\n" % (
                                        reading_id.record_id.reading_value)))
                if len(messages) > 0:
                    raise exceptions.ValidationError(_("Error while updating reading of asset [%s] %s. " + "\n".join(messages)) % (
                        # reading_id.object_id.code, record_id.object_id.resource_id.name))
                        reading_id.asset_id.code, record_id.asset_id.name))

        context['op'] = 'template'

        asset_ids = []
        for record in self:
            asset_template_ids = []
            for object_template in record.asset_template_ids:
                asset_template_ids.append(object_template.id)
                # object_ids.append(object_template.object_id.id)
                asset_ids.append(object_template.asset_id.id)

            record.asset_template_ids.initialize_wizard()
            context['asset_ids'] = asset_ids
            context['date_initial_schedule'] = record.date_initial_schedule
        return {
            'name': _('Initialized Schedules'),
            # 'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'df.maintenance.preventive.schedule',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': context
        }


    def asociate_object_template(self):
        self.ensure_one()
        reading = False
        for object_template in self.asset_template_ids:
            if object_template.regimen != 'calendar':
                reading = True
                break
        if reading:
            for object_template in self.asset_template_ids:
                object_template.reading_record_wizard_ids.unlink()
            self.asset_template_ids.generate_reading_record_wizard()
            form_res = self.env.ref(
                'l10n_cu_maintenance_preventive.df_maintenance_preventive_initialize_meter_readings_form_view')
            form_id = form_res and form_res.id or False
            return {
                'name': _('Initialize Meter Readings'),
                # 'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'df.maintenance.initialize.schedule',
                'res_id': int(self._ids[0]),
                'view_id': False,
                'views': [(form_id, 'form')],
                'target': 'new',
                'context': {'op': 'reading'},
                'type': 'ir.actions.act_window',
            }
        else:
            return self.initialize()


    def back_initialize(self):
        context = self._context.copy() or {}
        context['op'] = 'template'
        mod_obj = self.env['ir.model.data']
        act_obj = self.env['ir.actions.act_window']

        result = mod_obj.get_object_reference('l10n_cu_maintenance_preventive',
                                              'df_action_maintenance_initialize_schedule_form')
        id = result and result[1] or False
        return result


class MaintenancePreventiveObjectTemplateWizard(models.TransientModel):
    _name = "df.maintenance.object.template"
    _description = "Object Template Association"


    @api.depends('reading_record_wizard_ids')
    def calc_text_uom_ids(self):
        text_uom_ids = ""
        for reading_record in self.reading_record_wizard_ids:
            text_uom_ids += "%s %s " % (str(reading_record.average_value), reading_record.uom_id.name)
        self.text_uom_ids = text_uom_ids

    date_initial_schedule = fields.Date(string="Initial Date Schedule", default=date.today())
    date_initial_schedule_wizard = fields.Date(related="initialize_schedule_id.date_initial_schedule",string="Initial Date Schedule", default=date.today())
    regimen = fields.Selection(related='template_id.regimen', readonly=True)
    reading_record_wizard_ids = fields.One2many('l10n_cu_maintenance_preventive.reading_record_wizard',
                                                    'object_template_wizard_id', 'Meter Readings')
    text_uom_ids = fields.Char(string='UOMs', compute='calc_text_uom_ids')

    initialize_schedule_id = fields.Many2one('df.maintenance.initialize.schedule',
                            'Initialize Schedule')
    asset_id = fields.Many2one('maintenance.equipment', 'Maintenance Asset',
                            ondelete='cascade', required=True)
    template_id = fields.Many2one('df.maintenance.template', 'Template',
                            ondelete='cascade', required=True)


    def generate_reading_record_wizard(self):
        reading_record_env = self.env['df.reading.record']
        for object_template in self:
            reading_records_wizard = []
            for intervention_template_id in object_template.template_id.intervention_ids:
                if intervention_template_id.regimen in ['reading', 'both']:
                    reading_id = reading_record_env.search([('asset_id', '=', object_template.asset_id.id),
                                                            ('uom_id', '=', intervention_template_id.uom_id.id)])
                    if reading_id:
                        reading_id = reading_id[0]
                        reading_records_wizard.append(
                            dict(last_reading_date=reading_id.reading_date,
                                 base_value=reading_id.base_value,
                                 last_reading_value=reading_id.reading_value,
                                 accumulated_value=reading_id.accumulated_value,
                                 average_value=reading_id.average_value,
                                 uom_id=reading_id.uom_id.id,
                                 is_history=True,
                                 intervention_template_id=intervention_template_id.id,
                                 reading_id=reading_id.id))
                    else:
                        reading_records_wizard.append(dict(uom_id=intervention_template_id.uom_id.id,
                                                           intervention_template_id=intervention_template_id.id))

            object_template.reading_record_wizard_ids = reading_records_wizard

    @api.model
    def default_get(self, fields):
        res = super(MaintenancePreventiveObjectTemplateWizard, self).default_get(fields)
        asset_id = self._context and self._context.get('asset_id', False)
        res['asset_id'] = asset_id
        return res


    @api.onchange('template_id', 'asset_id')
    def onchange_object_template(self):
        if self.template_id and self.asset_id:
            self.generate_reading_record_wizard()
        else:
            self.reading_record_wizard_ids.unlink()


    def initialize(self):
        meter_wizard = self.env['l10n_cu_maintenance_preventive.reading_record_wizard']
        schedule_env = self.env['df.maintenance.schedule']
        meter_reading_env = self.env['df.reading.record']
        intervention_template_env = self.env['df.maintenance.intervention.template']
        for object_template in self:
            for intervention_template in object_template.template_id.intervention_ids:
                reading_id = False
                if intervention_template.reading:
                    meter_id = meter_wizard.search([('uom_id', '=', intervention_template.uom_id.id),
                                                    ('object_template_wizard_id', '=', object_template.id)])[0]
                    accumulated_value = meter_id.last_reading_value + meter_id.base_value
                    meter_reading_vals = dict(
                        # resource_id=object_template.object_id.id,
                        asset_id=object_template.asset_id.id,
                        uom_id=meter_id.uom_id.id,
                        accumulated_value=accumulated_value,
                        average_value=meter_id.average_value,
                        reading_date=object_template.date_initial_schedule,
                        reading_value=meter_id.last_reading_value,
                        base_value=meter_id.base_value)
                    if not meter_id.reading_id:
                        # create meter reading
                        meter_reading_vals.update(dict(action='create'))
                        reading_id = meter_reading_env.create(meter_reading_vals)
                    else:
                        reading_id = meter_id.reading_id
                        meter_reading_vals.update(dict(action='update'))
                        meter_id.reading_id.write(meter_reading_vals)

                    schedule_reading = schedule_env.create(
                        dict(asset_id=object_template.asset_id.id,
                             next_execution_reading=intervention_template.reading_frequency + reading_id.reading_value,
                             date_initial_schedule=object_template.date_initial_schedule,
                             frequency_schedule=intervention_template.interval,
                             reading_frequency=intervention_template.reading_frequency,
                             intervention_template_id=intervention_template.id,
                             reading_id=reading_id.id,
                             ))

                if intervention_template.calendar:
                    schedule_calendar = schedule_env.create(dict(asset_id=object_template.asset_id.id,
                                                                 date_initial_schedule=object_template.date_initial_schedule,
                                                                 # template_id=object_template.template_id.id,
                                                                 intervention_template_id=intervention_template.id,
                                                                 next_execution_schedule=intervention_template_env._get_next_excecution_date(
                                                                     intervention_template,
                                                                     object_template.date_initial_schedule),
                                                                 reading_id=reading_id and reading_id.id or False,
                                                                 frequency_schedule=intervention_template.interval,
                                                                 reading_frequency=intervention_template.reading_frequency,
                                                                 next_execution_reading=reading_id and intervention_template.reading_frequency + reading_id.reading_value or False,
                                                                 ))
                if intervention_template.calendar and intervention_template.reading:
                    if schedule_reading.next_reading_date < schedule_calendar.next_execution_schedule:
                        schedule_calendar.unlink()
                    else:
                        schedule_reading.unlink()
            object_template.asset_id.maintenance_template_id = object_template.template_id


    def initialize_wizard(self):
        meter_wizard = self.env['l10n_cu_maintenance_preventive.reading_record_wizard']
        schedule_env = self.env['df.maintenance.schedule']
        meter_reading_env = self.env['df.reading.record']
        intervention_template_env = self.env['df.maintenance.intervention.template']
        for object_template in self:
            for intervention_template in object_template.template_id.intervention_ids:
                reading_id = False
                if intervention_template.reading:
                    meter_id = meter_wizard.search([('uom_id', '=', intervention_template.uom_id.id),
                                                    ('object_template_wizard_id', '=', object_template.id)])[0]
                    accumulated_value = meter_id.last_reading_value + meter_id.base_value
                    meter_reading_vals = dict(
                        asset_id=object_template.asset_id.id,
                        uom_id=meter_id.uom_id.id,
                        accumulated_value=accumulated_value,
                        average_value=meter_id.average_value,
                        reading_date=object_template.date_initial_schedule_wizard,
                        reading_value=meter_id.last_reading_value,
                        base_value=meter_id.base_value)
                    if not meter_id.reading_id:
                        # create meter reading
                        meter_reading_vals.update(dict(action='create'))
                        reading_id = meter_reading_env.create(meter_reading_vals)
                    else:
                        reading_id = meter_id.reading_id
                        meter_reading_vals.update(dict(action='update'))
                        meter_id.reading_id.write(meter_reading_vals)

                    schedule_reading = schedule_env.create(
                        dict(asset_id=object_template.asset_id.id,
                             next_execution_reading=intervention_template.reading_frequency + reading_id.reading_value,
                             date_initial_schedule=object_template.date_initial_schedule_wizard,
                             frequency_schedule=intervention_template.interval,
                             reading_frequency=intervention_template.reading_frequency,
                             intervention_template_id=intervention_template.id,
                             reading_id=reading_id.id,
                             ))

                if intervention_template.calendar:
                    schedule_calendar = schedule_env.create(dict(
                                                                 asset_id=object_template.asset_id.id,
                                                                 date_initial_schedule=object_template.date_initial_schedule_wizard,
                                                                 template_id=object_template.template_id.id,
                                                                 intervention_template_id=intervention_template.id,
                                                                 next_execution_schedule=intervention_template_env._get_next_excecution_date(
                                                                     intervention_template,
                                                                     object_template.date_initial_schedule_wizard),
                                                                 reading_id=reading_id and reading_id.id or False,
                                                                 frequency_schedule=intervention_template.interval,
                                                                 reading_frequency=intervention_template.reading_frequency,
                                                                 next_execution_reading=reading_id and intervention_template.reading_frequency + reading_id.reading_value or False,
                                                                 ))
                if intervention_template.calendar and intervention_template.reading:
                    if schedule_reading.next_reading_date < schedule_calendar.next_execution_schedule:
                        schedule_calendar.unlink()
                    else:
                        schedule_reading.unlink()
            object_template.asset_id.maintenance_template_id = object_template.template_id
            object_template.asset_id.maintenance_template_id = object_template.template_id

    @api.model
    def initialize_action(self):
        self.initialize()
        return {'type': 'ir.actions.act_window_close'}


class MaintenancePreventiveMeterReadingObjectWizard(models.TransientModel):
    _name = 'l10n_cu_maintenance_preventive.reading_record_wizard'

    asset_id = fields.Many2one('maintenance.equipment', 'Maintenance Asset',
                                related='object_template_wizard_id.asset_id')
    last_reading_date = fields.Date('Last Reading Date')
    base_value = fields.Float('Base Value', attrs="{'readonly': [('is_history','=', True)]}")
    last_reading_value = fields.Float('Last Reading Value')
    accumulated_value = fields.Float('Accumulated Value')
    average_value = fields.Float('Daily Average Usage')
    uom_id = fields.Many2one('product.uom', 'Meter', required=True)
    object_template_wizard_id = fields.Many2one('df.maintenance.object.template')
    is_history = fields.Boolean()
    reading_id = fields.Many2one('df.reading.record')
    intervention_template_id = fields.Many2one('df.maintenance.intervention.template')

    @api.onchange('base_value', 'last_reading_value')
    def onchange_last_reading_value(self):
        self.accumulated_value = self.last_reading_value + self.base_value


class MaintenancePreventiveScheduleWizard(models.TransientModel):
    _name = "df.maintenance.preventive.schedule"
    _description = "Initialized Schedules"

    def open_technical_records(self):
        context = dict(self._context or {})
        context['is_mtto'] = True
        mod_obj = self.env['ir.model.data']
        act_obj = self.env['ir.actions.act_window']
        result = mod_obj.get_object_reference('asset', 'assets_tree_view')
        id = result and result[1] or False
        domain = [('id','in',context.get('asset_ids', False))]
        return {
            'name': 'Maintenance Assett',
            # 'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'maintenance.equipment',
            'type': 'ir.actions.act_window',
            'res_id': id,
            'search_view_id': self.env.ref('l10n_cu_maintenance.assets_maintenance_tree_view').id,
            'domain': domain,
            'context': context
        }