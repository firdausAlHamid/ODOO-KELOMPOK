# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class BureaucracyTicketCategory(models.Model):
    """
    Kategori tiket untuk mengklasifikasikan jenis kerusakan.
    Contoh: Elektronik, Furniture, Jaringan, Infrastruktur, dll.
    """
    _name = 'bureaucracy.ticket.category'
    _description = 'Kategori Tiket Pelaporan'
    _order = 'sequence, name'

    name = fields.Char(
        string='Nama Kategori',
        required=True,
        help='Contoh: Elektronik, Furniture, Jaringan',
    )
    code = fields.Char(
        string='Kode',
        required=True,
        help='Kode singkat kategori, contoh: ELK, FRN, NET',
    )
    description = fields.Text(
        string='Deskripsi',
        help='Penjelasan detail mengenai kategori ini.',
    )
    sequence = fields.Integer(
        string='Urutan',
        default=10,
    )
    active = fields.Boolean(
        string='Aktif',
        default=True,
    )
    color = fields.Integer(
        string='Warna',
    )
    ticket_ids = fields.One2many(
        'bureaucracy.ticket',
        'category_id',
        string='Tiket',
    )
    ticket_count = fields.Integer(
        string='Jumlah Tiket',
        compute='_compute_ticket_count',
    )

    @api.depends('ticket_ids')
    def _compute_ticket_count(self):
        for record in self:
            record.ticket_count = len(record.ticket_ids)

    _constraints = [
        models.Constraint('UNIQUE(code)', message='Kode kategori harus unik!'),
    ]
