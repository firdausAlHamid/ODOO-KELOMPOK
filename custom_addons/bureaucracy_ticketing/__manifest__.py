# -*- coding: utf-8 -*-
{
    'name': 'Bureaucracy Ticketing - Sistem Pelaporan Fasilitas',
    'version': '19.0.1.0.0',
    'category': 'Services/Helpdesk',
    'summary': 'Sistem pelaporan kerusakan fasilitas kampus terintegrasi dengan HR',
    'description': """
==========================================
Bureaucracy Ticketing System
==========================================

Modul ini menyediakan sistem pelaporan kerusakan fasilitas kampus
yang terintegrasi dengan modul HR Odoo. Fitur utama:

* Pelaporan kerusakan fasilitas (proyektor, AC, komputer, dll)
* Workflow status: Draft → Submitted → In Progress → Resolved / Cancelled
* Integrasi dengan modul HR (data karyawan/dosen & departemen)
* Sistem kategori tiket (Elektronik, Furniture, Jaringan, dll)
* Log komentar / catatan penanganan
* Dashboard statistik tiket
* REST API (Open API) untuk integrasi sistem eksternal
* Auto-generate nomor tiket (sequence)
* Priority level & SLA tracking
    """,
    'author': 'Kelompok Odoo',
    'website': 'https://github.com/kelompok-odoo',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'hr',
        'mail',
    ],
    'data': [
        # Security
        'security/ticketing_security.xml',
        'security/ir.model.access.csv',
        # Data
        'data/sequence_data.xml',
        'data/category_data.xml',
        # Views
        'views/ticket_comment_views.xml',
        'views/ticket_category_views.xml',
        'views/ticket_views.xml',
        'views/menu_views.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'sequence': 10,
}
