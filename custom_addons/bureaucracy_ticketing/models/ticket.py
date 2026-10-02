# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class BureaucracyTicket(models.Model):
    """
    Model utama untuk tiket pelaporan kerusakan fasilitas.
    Terintegrasi dengan modul HR untuk data pelapor (karyawan/dosen)
    dan departemen.
    """
    _name = 'bureaucracy.ticket'
    _description = 'Ticket Pelaporan Birokrasi'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'
    _rec_name = 'name'

    # =====================
    # FIELDS
    # =====================

    # --- Identitas Tiket ---
    name = fields.Char(
        string='Nomor Tiket',
        required=True,
        copy=False,
        readonly=True,
        index=True,
        default=lambda self: _('New'),
        help='Nomor tiket otomatis di-generate oleh sistem.',
    )
    title = fields.Char(
        string='Judul Laporan',
        required=True,
        tracking=True,
        help='Contoh: Proyektor di Ruang 101 Rusak',
    )
    description = fields.Html(
        string='Deskripsi Lengkap',
        required=True,
        help='Jelaskan detail kerusakan yang terjadi.',
    )

    # --- Integrasi HR (Pelapor) ---
    employee_id = fields.Many2one(
        'hr.employee',
        string='Pelapor',
        default=lambda self: self.env.user.employee_id,
        required=True,
        tracking=True,
        help='Karyawan/dosen yang melaporkan kerusakan. '
             'Otomatis terisi dari user yang login.',
    )
    department_id = fields.Many2one(
        'hr.department',
        string='Departemen / Fakultas',
        related='employee_id.department_id',
        store=True,
        readonly=True,
        help='Departemen pelapor, otomatis dari data HR.',
    )
    employee_job_title = fields.Char(
        string='Jabatan Pelapor',
        related='employee_id.job_title',
        store=True,
        readonly=True,
    )
    employee_phone = fields.Char(
        string='No. Telepon Pelapor',
        related='employee_id.work_phone',
        readonly=True,
    )
    employee_email = fields.Char(
        string='Email Pelapor',
        related='employee_id.work_email',
        readonly=True,
    )

    # --- Klasifikasi Tiket ---
    category_id = fields.Many2one(
        'bureaucracy.ticket.category',
        string='Kategori',
        required=True,
        tracking=True,
        help='Kategori kerusakan: Elektronik, Furniture, Jaringan, dll.',
    )
    location = fields.Char(
        string='Lokasi Kerusakan',
        required=True,
        help='Contoh: Gedung A, Lantai 2, Ruang 201',
    )
    priority = fields.Selection(
        selection=[
            ('0', 'Rendah'),
            ('1', 'Sedang'),
            ('2', 'Tinggi'),
            ('3', 'Sangat Mendesak'),
        ],
        string='Prioritas',
        default='1',
        tracking=True,
        help='Tingkat urgensi penanganan.',
    )

    # --- Status & Workflow ---
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('submitted', 'Diajukan'),
            ('in_progress', 'Sedang Diproses'),
            ('resolved', 'Selesai'),
            ('cancelled', 'Dibatalkan'),
        ],
        string='Status',
        default='draft',
        tracking=True,
        copy=False,
        help='Alur status tiket dari pembuatan hingga penyelesaian.',
    )

    # --- Tanggal ---
    report_date = fields.Datetime(
        string='Tanggal Laporan',
        default=fields.Datetime.now,
        readonly=True,
    )
    date_submitted = fields.Datetime(
        string='Tanggal Diajukan',
        readonly=True,
    )
    date_in_progress = fields.Datetime(
        string='Tanggal Mulai Diproses',
        readonly=True,
    )
    date_resolved = fields.Datetime(
        string='Tanggal Selesai',
        readonly=True,
    )
    date_cancelled = fields.Datetime(
        string='Tanggal Dibatalkan',
        readonly=True,
    )

    # --- Penugasan (PIC) ---
    assigned_to = fields.Many2one(
        'hr.employee',
        string='Ditugaskan Kepada (PIC)',
        tracking=True,
        help='Teknisi/staf yang ditugaskan menangani tiket ini.',
    )
    assigned_department_id = fields.Many2one(
        'hr.department',
        string='Departemen PIC',
        related='assigned_to.department_id',
        store=True,
        readonly=True,
    )

    # --- Resolusi ---
    resolution_note = fields.Html(
        string='Catatan Penyelesaian',
        help='Penjelasan apa yang dilakukan untuk menyelesaikan masalah.',
    )

    # --- Komentar / Log ---
    comment_ids = fields.One2many(
        'bureaucracy.ticket.comment',
        'ticket_id',
        string='Log Penanganan',
    )
    comment_count = fields.Integer(
        string='Jumlah Komentar',
        compute='_compute_comment_count',
    )

    # --- Computed Fields ---
    is_overdue = fields.Boolean(
        string='Terlambat',
        compute='_compute_is_overdue',
        store=True,
    )
    duration_days = fields.Float(
        string='Durasi (Hari)',
        compute='_compute_duration_days',
        store=True,
        help='Durasi dari tanggal laporan sampai selesai/sekarang.',
    )
    color = fields.Integer(string='Warna Kanban')

    # =====================
    # COMPUTE METHODS
    # =====================

    @api.depends('comment_ids')
    def _compute_comment_count(self):
        for record in self:
            record.comment_count = len(record.comment_ids)

    @api.depends('report_date', 'date_resolved', 'state')
    def _compute_duration_days(self):
        for record in self:
            if record.report_date:
                end_date = record.date_resolved or fields.Datetime.now()
                delta = end_date - record.report_date
                record.duration_days = delta.days + (delta.seconds / 86400.0)
            else:
                record.duration_days = 0

    @api.depends('report_date', 'state', 'priority')
    def _compute_is_overdue(self):
        """Tiket dianggap overdue jika belum selesai melebihi SLA berdasarkan prioritas."""
        sla_days = {'0': 7, '1': 5, '2': 3, '3': 1}
        for record in self:
            if record.state in ('resolved', 'cancelled') or not record.report_date:
                record.is_overdue = False
            else:
                max_days = sla_days.get(record.priority, 5)
                delta = fields.Datetime.now() - record.report_date
                record.is_overdue = delta.days > max_days

    # =====================
    # CRUD OVERRIDES
    # =====================

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'bureaucracy.ticket'
                ) or _('New')
        return super().create(vals_list)

    def unlink(self):
        for record in self:
            if record.state not in ('draft', 'cancelled'):
                raise UserError(
                    _('Tidak bisa menghapus tiket yang sudah diajukan atau diproses. '
                      'Batalkan terlebih dahulu.')
                )
        return super().unlink()

    # =====================
    # ACTION METHODS (WORKFLOW)
    # =====================

    def action_submit(self):
        """Submit tiket dari Draft ke Diajukan."""
        for record in self:
            if record.state != 'draft':
                raise UserError(_('Hanya tiket berstatus Draft yang bisa diajukan.'))
            record.write({
                'state': 'submitted',
                'date_submitted': fields.Datetime.now(),
            })

    def action_in_progress(self):
        """Mulai proses penanganan tiket."""
        for record in self:
            if record.state != 'submitted':
                raise UserError(_('Hanya tiket yang sudah diajukan yang bisa diproses.'))
            if not record.assigned_to:
                raise UserError(_('Harap tentukan PIC (Ditugaskan Kepada) sebelum memproses tiket.'))
            record.write({
                'state': 'in_progress',
                'date_in_progress': fields.Datetime.now(),
            })

    def action_resolve(self):
        """Tandai tiket sebagai selesai."""
        for record in self:
            if record.state != 'in_progress':
                raise UserError(_('Hanya tiket yang sedang diproses yang bisa diselesaikan.'))
            record.write({
                'state': 'resolved',
                'date_resolved': fields.Datetime.now(),
            })

    def action_cancel(self):
        """Batalkan tiket."""
        for record in self:
            if record.state == 'resolved':
                raise UserError(_('Tiket yang sudah selesai tidak bisa dibatalkan.'))
            record.write({
                'state': 'cancelled',
                'date_cancelled': fields.Datetime.now(),
            })

    def action_reset_draft(self):
        """Reset tiket kembali ke Draft."""
        for record in self:
            if record.state not in ('cancelled', 'submitted'):
                raise UserError(
                    _('Hanya tiket yang dibatalkan atau diajukan yang bisa di-reset ke Draft.')
                )
            record.write({
                'state': 'draft',
                'date_submitted': False,
                'date_in_progress': False,
                'date_resolved': False,
                'date_cancelled': False,
            })
