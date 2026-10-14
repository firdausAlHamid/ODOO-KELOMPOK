# -*- coding: utf-8 -*-
"""Models for IT Hardware Request addon."""

from odoo import models, fields, api, _

class ItHardwareRequest(models.Model):
    _name = "it.hardware.request"
    _description = "IT Hardware Request"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc, id desc"

    name = fields.Char(string="Request Reference", required=True, copy=False, readonly=True, default=lambda self: _("New"))
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, default=lambda self: self.env.user.employee_id)
    title = fields.Char(string='Title', required=True, tracking=True)
    description = fields.Text(string='Description')
    category_id = fields.Many2one('product.category', string='Category', required=True, tracking=True)
    location = fields.Char(string='Location')
    quantity = fields.Float(string='Quantity', default=1.0)
    priority = fields.Selection([
        ("0", "Low"),
        ("1", "Medium"),
        ("2", "High"),
        ("3", "Very High"),
    ], string='Priority', default="1", tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('to_approve', 'Waiting Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('delivered', 'Delivered'),
    ], string='Status', default='draft', tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('it.hardware.request') or _('New')
        return super().create(vals_list)
