# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class BureaucracyTicketComment(models.Model):
    """
    Log komentar/catatan penanganan pada tiket.
    Digunakan untuk mencatat progress dan komunikasi
    antara pelapor dan teknisi.
    """
    _name = 'bureaucracy.ticket.comment'
    _description = 'Komentar / Log Penanganan Tiket'
    _order = 'create_date desc'

    ticket_id = fields.Many2one(
        'bureaucracy.ticket',
        string='Tiket',
        required=True,
        ondelete='cascade',
    )
    author_id = fields.Many2one(
        'hr.employee',
        string='Penulis',
        default=lambda self: self.env.user.employee_id,
        required=True,
    )
    body = fields.Html(
        string='Isi Komentar',
        required=True,
    )
    comment_type = fields.Selection(
        selection=[
            ('comment', 'Komentar'),
            ('update', 'Update Progress'),
            ('internal', 'Catatan Internal'),
        ],
        string='Tipe',
        default='comment',
        required=True,
    )
    attachment_ids = fields.Many2many(
        'ir.attachment',
        string='Lampiran',
    )
