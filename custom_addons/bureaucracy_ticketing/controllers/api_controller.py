# -*- coding: utf-8 -*-
"""
REST API Controller untuk Bureaucracy Ticketing System.

Menyediakan Open API endpoints agar sistem lain bisa
mengakses dan mengintegrasikan data tiket pelaporan.

Endpoints yang tersedia:
    GET    /api/v1/tickets          - Daftar semua tiket
    GET    /api/v1/tickets/<id>     - Detail tiket tertentu
    POST   /api/v1/tickets          - Buat tiket baru
    PUT    /api/v1/tickets/<id>     - Update tiket
    DELETE /api/v1/tickets/<id>     - Hapus tiket
    GET    /api/v1/tickets/categories - Daftar kategori
    GET    /api/v1/tickets/stats    - Statistik tiket

Autentikasi menggunakan session Odoo (cookie-based)
atau API Key via header.
"""

import json
import logging
from datetime import datetime

from odoo import http, fields, _
from odoo.http import request, Response

_logger = logging.getLogger(__name__)


class BureaucracyTicketingAPI(http.Controller):
    """
    REST API Controller untuk sistem pelaporan fasilitas.
    Menyediakan endpoint CRUD dan statistik yang bisa diakses
    oleh sistem eksternal.
    """

    # =============================================
    # Helper Methods
    # =============================================

    def _json_response(self, data, status=200):
        """Helper untuk mengembalikan JSON response yang konsisten."""
        body = json.dumps(data, default=str, ensure_ascii=False)
        return Response(
            body,
            status=status,
            content_type='application/json; charset=utf-8',
        )

    def _serialize_ticket(self, ticket):
        """Serialize record tiket ke dictionary untuk JSON response."""
        return {
            'id': ticket.id,
            'name': ticket.name,
            'title': ticket.title,
            'description': ticket.description or '',
            'location': ticket.location,
            'priority': ticket.priority,
            'priority_label': dict(ticket._fields['priority'].selection).get(
                ticket.priority, ''
            ),
            'state': ticket.state,
            'state_label': dict(ticket._fields['state'].selection).get(
                ticket.state, ''
            ),
            # Integrasi HR
            'employee': {
                'id': ticket.employee_id.id,
                'name': ticket.employee_id.name,
                'job_title': ticket.employee_job_title or '',
                'email': ticket.employee_email or '',
                'phone': ticket.employee_phone or '',
            } if ticket.employee_id else None,
            'department': {
                'id': ticket.department_id.id,
                'name': ticket.department_id.name,
            } if ticket.department_id else None,
            'category': {
                'id': ticket.category_id.id,
                'name': ticket.category_id.name,
                'code': ticket.category_id.code,
            } if ticket.category_id else None,
            'assigned_to': {
                'id': ticket.assigned_to.id,
                'name': ticket.assigned_to.name,
            } if ticket.assigned_to else None,
            # Tanggal
            'report_date': ticket.report_date,
            'date_submitted': ticket.date_submitted,
            'date_in_progress': ticket.date_in_progress,
            'date_resolved': ticket.date_resolved,
            'date_cancelled': ticket.date_cancelled,
            # Computed
            'is_overdue': ticket.is_overdue,
            'duration_days': round(ticket.duration_days, 2),
            'resolution_note': ticket.resolution_note or '',
            'comment_count': ticket.comment_count,
        }

    def _serialize_category(self, category):
        """Serialize record kategori ke dictionary."""
        return {
            'id': category.id,
            'name': category.name,
            'code': category.code,
            'description': category.description or '',
            'ticket_count': category.ticket_count,
        }

    # =============================================
    # API Endpoints - CRUD Tickets
    # =============================================

    @http.route(
        '/api/v1/tickets',
        type='http',
        auth='user',
        methods=['GET'],
        csrf=False,
    )
    def get_tickets(self, **kwargs):
        """
        GET /api/v1/tickets
        Mendapatkan daftar semua tiket.

        Query Parameters:
            - state: filter by status (draft, submitted, in_progress, resolved, cancelled)
            - priority: filter by prioritas (0, 1, 2, 3)
            - category_id: filter by kategori ID
            - department_id: filter by departemen ID
            - employee_id: filter by pelapor ID
            - assigned_to: filter by PIC ID
            - limit: jumlah data per halaman (default: 50)
            - offset: offset untuk pagination (default: 0)
            - order: urutan (default: create_date desc)

        Returns:
            JSON list of tickets
        """
        try:
            domain = []

            # Apply filters
            if kwargs.get('state'):
                domain.append(('state', '=', kwargs['state']))
            if kwargs.get('priority'):
                domain.append(('priority', '=', kwargs['priority']))
            if kwargs.get('category_id'):
                domain.append(('category_id', '=', int(kwargs['category_id'])))
            if kwargs.get('department_id'):
                domain.append(('department_id', '=', int(kwargs['department_id'])))
            if kwargs.get('employee_id'):
                domain.append(('employee_id', '=', int(kwargs['employee_id'])))
            if kwargs.get('assigned_to'):
                domain.append(('assigned_to', '=', int(kwargs['assigned_to'])))

            limit = int(kwargs.get('limit', 50))
            offset = int(kwargs.get('offset', 0))
            order = kwargs.get('order', 'create_date desc')

            tickets = request.env['bureaucracy.ticket'].sudo().search(
                domain, limit=limit, offset=offset, order=order
            )
            total = request.env['bureaucracy.ticket'].sudo().search_count(domain)

            data = {
                'status': 'success',
                'total': total,
                'limit': limit,
                'offset': offset,
                'data': [self._serialize_ticket(t) for t in tickets],
            }
            return self._json_response(data)

        except Exception as e:
            _logger.error('API Error GET /api/v1/tickets: %s', str(e))
            return self._json_response({
                'status': 'error',
                'message': str(e),
            }, status=500)

    @http.route(
        '/api/v1/tickets/<int:ticket_id>',
        type='http',
        auth='user',
        methods=['GET'],
        csrf=False,
    )
    def get_ticket(self, ticket_id, **kwargs):
        """
        GET /api/v1/tickets/<id>
        Mendapatkan detail satu tiket berdasarkan ID.

        Returns:
            JSON detail ticket
        """
        try:
            ticket = request.env['bureaucracy.ticket'].sudo().browse(ticket_id)
            if not ticket.exists():
                return self._json_response({
                    'status': 'error',
                    'message': f'Tiket dengan ID {ticket_id} tidak ditemukan.',
                }, status=404)

            # Include comments in detail view
            ticket_data = self._serialize_ticket(ticket)
            ticket_data['comments'] = [{
                'id': c.id,
                'author': c.author_id.name if c.author_id else '',
                'body': c.body or '',
                'type': c.comment_type,
                'created_at': c.create_date,
            } for c in ticket.comment_ids]

            return self._json_response({
                'status': 'success',
                'data': ticket_data,
            })

        except Exception as e:
            _logger.error('API Error GET /api/v1/tickets/%s: %s', ticket_id, str(e))
            return self._json_response({
                'status': 'error',
                'message': str(e),
            }, status=500)

    @http.route(
        '/api/v1/tickets',
        type='http',
        auth='user',
        methods=['POST'],
        csrf=False,
    )
    def create_ticket(self, **kwargs):
        """
        POST /api/v1/tickets
        Membuat tiket baru.

        Request Body (JSON):
            - title: (required) Judul laporan
            - description: (required) Deskripsi kerusakan
            - category_id: (required) ID kategori
            - location: (required) Lokasi kerusakan
            - employee_id: (optional) ID pelapor, default user yang login
            - priority: (optional) 0-3, default 1
            - assigned_to: (optional) ID PIC

        Returns:
            JSON created ticket
        """
        try:
            # Parse JSON body
            body = json.loads(request.httprequest.data or '{}')

            # Validasi required fields
            required_fields = ['title', 'description', 'category_id', 'location']
            missing = [f for f in required_fields if not body.get(f)]
            if missing:
                return self._json_response({
                    'status': 'error',
                    'message': f'Field wajib yang belum diisi: {", ".join(missing)}',
                }, status=400)

            vals = {
                'title': body['title'],
                'description': body['description'],
                'category_id': int(body['category_id']),
                'location': body['location'],
                'priority': body.get('priority', '1'),
            }

            if body.get('employee_id'):
                vals['employee_id'] = int(body['employee_id'])
            else:
                # Default ke employee dari user yang login
                employee = request.env.user.employee_id
                if employee:
                    vals['employee_id'] = employee.id
                else:
                    return self._json_response({
                        'status': 'error',
                        'message': 'User tidak memiliki data karyawan di HR. '
                                   'Silakan kirim employee_id secara manual.',
                    }, status=400)

            if body.get('assigned_to'):
                vals['assigned_to'] = int(body['assigned_to'])

            ticket = request.env['bureaucracy.ticket'].sudo().create(vals)

            return self._json_response({
                'status': 'success',
                'message': 'Tiket berhasil dibuat.',
                'data': self._serialize_ticket(ticket),
            }, status=201)

        except json.JSONDecodeError:
            return self._json_response({
                'status': 'error',
                'message': 'Invalid JSON body.',
            }, status=400)
        except Exception as e:
            _logger.error('API Error POST /api/v1/tickets: %s', str(e))
            return self._json_response({
                'status': 'error',
                'message': str(e),
            }, status=500)

    @http.route(
        '/api/v1/tickets/<int:ticket_id>',
        type='http',
        auth='user',
        methods=['PUT'],
        csrf=False,
    )
    def update_ticket(self, ticket_id, **kwargs):
        """
        PUT /api/v1/tickets/<id>
        Update data tiket.

        Request Body (JSON):
            - title: Judul laporan
            - description: Deskripsi
            - category_id: ID kategori
            - location: Lokasi
            - priority: Prioritas (0-3)
            - assigned_to: ID PIC
            - state: Status baru (akan trigger workflow action)
            - resolution_note: Catatan penyelesaian

        Returns:
            JSON updated ticket
        """
        try:
            ticket = request.env['bureaucracy.ticket'].sudo().browse(ticket_id)
            if not ticket.exists():
                return self._json_response({
                    'status': 'error',
                    'message': f'Tiket dengan ID {ticket_id} tidak ditemukan.',
                }, status=404)

            body = json.loads(request.httprequest.data or '{}')
            vals = {}

            # Update fields yang dikirim
            updatable_fields = [
                'title', 'description', 'location', 'priority',
                'resolution_note',
            ]
            for field in updatable_fields:
                if field in body:
                    vals[field] = body[field]

            if 'category_id' in body:
                vals['category_id'] = int(body['category_id'])
            if 'assigned_to' in body:
                vals['assigned_to'] = int(body['assigned_to'])
            if 'employee_id' in body:
                vals['employee_id'] = int(body['employee_id'])

            if vals:
                ticket.write(vals)

            # Handle state change via workflow actions
            if 'state' in body:
                state_actions = {
                    'submitted': ticket.action_submit,
                    'in_progress': ticket.action_in_progress,
                    'resolved': ticket.action_resolve,
                    'cancelled': ticket.action_cancel,
                    'draft': ticket.action_reset_draft,
                }
                action = state_actions.get(body['state'])
                if action:
                    action()
                else:
                    return self._json_response({
                        'status': 'error',
                        'message': f'Status "{body["state"]}" tidak valid.',
                    }, status=400)

            return self._json_response({
                'status': 'success',
                'message': 'Tiket berhasil diupdate.',
                'data': self._serialize_ticket(ticket),
            })

        except json.JSONDecodeError:
            return self._json_response({
                'status': 'error',
                'message': 'Invalid JSON body.',
            }, status=400)
        except Exception as e:
            _logger.error('API Error PUT /api/v1/tickets/%s: %s', ticket_id, str(e))
            return self._json_response({
                'status': 'error',
                'message': str(e),
            }, status=500)

    @http.route(
        '/api/v1/tickets/<int:ticket_id>',
        type='http',
        auth='user',
        methods=['DELETE'],
        csrf=False,
    )
    def delete_ticket(self, ticket_id, **kwargs):
        """
        DELETE /api/v1/tickets/<id>
        Hapus tiket (hanya yang status Draft atau Cancelled).

        Returns:
            JSON confirmation
        """
        try:
            ticket = request.env['bureaucracy.ticket'].sudo().browse(ticket_id)
            if not ticket.exists():
                return self._json_response({
                    'status': 'error',
                    'message': f'Tiket dengan ID {ticket_id} tidak ditemukan.',
                }, status=404)

            ticket_name = ticket.name
            ticket.unlink()

            return self._json_response({
                'status': 'success',
                'message': f'Tiket {ticket_name} berhasil dihapus.',
            })

        except Exception as e:
            _logger.error('API Error DELETE /api/v1/tickets/%s: %s', ticket_id, str(e))
            return self._json_response({
                'status': 'error',
                'message': str(e),
            }, status=500)

    # =============================================
    # API Endpoints - Categories
    # =============================================

    @http.route(
        '/api/v1/tickets/categories',
        type='http',
        auth='user',
        methods=['GET'],
        csrf=False,
    )
    def get_categories(self, **kwargs):
        """
        GET /api/v1/tickets/categories
        Mendapatkan daftar semua kategori tiket.

        Returns:
            JSON list of categories
        """
        try:
            categories = request.env['bureaucracy.ticket.category'].sudo().search(
                [('active', '=', True)], order='sequence'
            )
            return self._json_response({
                'status': 'success',
                'data': [self._serialize_category(c) for c in categories],
            })
        except Exception as e:
            _logger.error('API Error GET /api/v1/tickets/categories: %s', str(e))
            return self._json_response({
                'status': 'error',
                'message': str(e),
            }, status=500)

    # =============================================
    # API Endpoints - Statistics
    # =============================================

    @http.route(
        '/api/v1/tickets/stats',
        type='http',
        auth='user',
        methods=['GET'],
        csrf=False,
    )
    def get_stats(self, **kwargs):
        """
        GET /api/v1/tickets/stats
        Mendapatkan statistik tiket.

        Returns:
            JSON statistics (total, by status, by priority, by category, etc.)
        """
        try:
            Ticket = request.env['bureaucracy.ticket'].sudo()

            # Count by state
            states = ['draft', 'submitted', 'in_progress', 'resolved', 'cancelled']
            by_state = {}
            for state in states:
                by_state[state] = Ticket.search_count([('state', '=', state)])

            # Count by priority
            priorities = ['0', '1', '2', '3']
            by_priority = {}
            priority_labels = {'0': 'Rendah', '1': 'Sedang', '2': 'Tinggi', '3': 'Sangat Mendesak'}
            for p in priorities:
                by_priority[priority_labels[p]] = Ticket.search_count([('priority', '=', p)])

            # Count by category
            categories = request.env['bureaucracy.ticket.category'].sudo().search([])
            by_category = {}
            for cat in categories:
                by_category[cat.name] = cat.ticket_count

            # Count overdue
            overdue_count = Ticket.search_count([('is_overdue', '=', True)])

            total = Ticket.search_count([])

            data = {
                'status': 'success',
                'data': {
                    'total_tickets': total,
                    'overdue_count': overdue_count,
                    'by_state': by_state,
                    'by_priority': by_priority,
                    'by_category': by_category,
                    'resolution_rate': round(
                        (by_state.get('resolved', 0) / total * 100) if total > 0 else 0, 2
                    ),
                },
            }
            return self._json_response(data)

        except Exception as e:
            _logger.error('API Error GET /api/v1/tickets/stats: %s', str(e))
            return self._json_response({
                'status': 'error',
                'message': str(e),
            }, status=500)

    # =============================================
    # API Endpoints - Employees (HR Integration)
    # =============================================

    @http.route(
        '/api/v1/employees',
        type='http',
        auth='user',
        methods=['GET'],
        csrf=False,
    )
    def get_employees(self, **kwargs):
        """
        GET /api/v1/employees
        Mendapatkan daftar karyawan dari modul HR.
        Berguna untuk frontend eksternal yang perlu memilih pelapor.

        Query Parameters:
            - department_id: filter by departemen
            - limit: jumlah data (default: 100)

        Returns:
            JSON list of employees
        """
        try:
            domain = []
            if kwargs.get('department_id'):
                domain.append(('department_id', '=', int(kwargs['department_id'])))

            limit = int(kwargs.get('limit', 100))
            employees = request.env['hr.employee'].sudo().search(
                domain, limit=limit, order='name'
            )

            data = {
                'status': 'success',
                'data': [{
                    'id': emp.id,
                    'name': emp.name,
                    'job_title': emp.job_title or '',
                    'department': {
                        'id': emp.department_id.id,
                        'name': emp.department_id.name,
                    } if emp.department_id else None,
                    'work_email': emp.work_email or '',
                    'work_phone': emp.work_phone or '',
                } for emp in employees],
            }
            return self._json_response(data)

        except Exception as e:
            _logger.error('API Error GET /api/v1/employees: %s', str(e))
            return self._json_response({
                'status': 'error',
                'message': str(e),
            }, status=500)

    @http.route(
        '/api/v1/departments',
        type='http',
        auth='user',
        methods=['GET'],
        csrf=False,
    )
    def get_departments(self, **kwargs):
        """
        GET /api/v1/departments
        Mendapatkan daftar departemen dari modul HR.

        Returns:
            JSON list of departments
        """
        try:
            departments = request.env['hr.department'].sudo().search(
                [], order='name'
            )
            data = {
                'status': 'success',
                'data': [{
                    'id': dept.id,
                    'name': dept.name,
                    'manager': {
                        'id': dept.manager_id.id,
                        'name': dept.manager_id.name,
                    } if dept.manager_id else None,
                    'total_employee': dept.total_employee,
                } for dept in departments],
            }
            return self._json_response(data)

        except Exception as e:
            _logger.error('API Error GET /api/v1/departments: %s', str(e))
            return self._json_response({
                'status': 'error',
                'message': str(e),
            }, status=500)
