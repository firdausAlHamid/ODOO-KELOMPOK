# -*- coding: utf-8 -*-
"""
REST API Controller for IT Hardware Request addon.
Provides GET and POST endpoints for hardware requests.
"""

import json
import logging
from odoo import http, _
from odoo.http import request, Response

_logger = logging.getLogger(__name__)


class ITHardwareRequestAPI(http.Controller):
    """CRUD endpoints for IT Hardware Request."""

    def _json_response(self, data, status=200):
        """Utility to return JSON with proper content-type."""
        body = json.dumps(data, default=str, ensure_ascii=False)
        return Response(
            body,
            status=status,
            content_type='application/json; charset=utf-8',
        )

    def _serialize_request(self, req):
        """Serialize it.hardware.request record to dict."""
        return {
            'id': req.id,
            'name': req.name,
            'title': req.title,
            'description': req.description or '',
            'category': {
                'id': req.category_id.id,
                'name': req.category_id.name,
            } if req.category_id else None,
            'location': req.location or '',
            'quantity': req.quantity,
            'priority': req.priority,
            'state': req.state,
            'employee': {
                'id': req.employee_id.id,
                'name': req.employee_id.name,
            } if req.employee_id else None,
            'create_date': req.create_date,
        }

    @http.route(
        '/api/v1/hardware_requests',
        type='http',
        auth='public',
        methods=['GET'],
        csrf=False,
        cors='*',
    )
    def get_hardware_requests(self, **kwargs):
        """GET /api/v1/hardware_requests - List all hardware requests."""
        try:
            requests = request.env['it.hardware.request'].sudo().search([], order='id desc')
            data = [self._serialize_request(r) for r in requests]
            return self._json_response({
                'status': 'success',
                'count': len(data),
                'data': data,
            })
        except Exception as e:
            _logger.error('API GET /api/v1/hardware_requests error: %s', str(e))
            return self._json_response({
                'status': 'error',
                'message': str(e),
            }, status=500)

    @http.route(
        '/api/v1/hardware_requests',
        type='http',
        auth='public',
        methods=['POST'],
        csrf=False,
        cors='*',
    )
    def create_hardware_request(self, **kw):
        """POST /api/v1/hardware_requests - Create a new hardware request."""
        try:
            payload = {}
            if request.httprequest.data:
                try:
                    payload = json.loads(request.httprequest.data.decode('utf-8'))
                except Exception:
                    payload = json.loads(request.httprequest.data)
            
            # If empty payload, try form data
            if not payload and request.params:
                payload = request.params

            # Validate required fields
            required = ['title', 'description', 'category_id', 'location']
            missing = [f for f in required if not payload.get(f)]
            if missing:
                return self._json_response({
                    'status': 'error',
                    'message': f'Field wajib belum diisi: {", ".join(missing)}',
                }, status=400)

            # Check / resolve category_id
            cat_id = int(payload['category_id'])
            category = request.env['product.category'].sudo().browse(cat_id)
            if not category.exists():
                first_cat = request.env['product.category'].sudo().search([], limit=1)
                if first_cat:
                    cat_id = first_cat.id
                else:
                    first_cat = request.env['product.category'].sudo().create({'name': 'All'})
                    cat_id = first_cat.id

            # Build vals for Odoo model it.hardware.request
            vals = {
                'title': payload['title'],
                'description': payload['description'],
                'category_id': cat_id,
                'location': payload['location'],
                'quantity': float(payload.get('quantity', 1.0)),
                'priority': str(payload.get('priority', "1")),
            }

            # Resolve employee
            if payload.get('employee_id'):
                vals['employee_id'] = int(payload['employee_id'])
            else:
                emp = request.env.user.employee_id if request.env.user and hasattr(request.env.user, 'employee_id') else None
                if emp:
                    vals['employee_id'] = emp.id
                else:
                    first_emp = request.env['hr.employee'].sudo().search([], limit=1)
                    if first_emp:
                        vals['employee_id'] = first_emp.id
                    else:
                        first_emp = request.env['hr.employee'].sudo().create({'name': 'Administrator'})
                        vals['employee_id'] = first_emp.id

            # Create the record
            new_req = request.env['it.hardware.request'].sudo().create(vals)

            return self._json_response({
                'status': 'success',
                'message': 'Permintaan hardware berhasil dibuat.',
                'data': self._serialize_request(new_req),
            }, status=201)

        except json.JSONDecodeError:
            return self._json_response({
                'status': 'error',
                'message': 'Format body JSON tidak valid.',
            }, status=400)
        except Exception as e:
            _logger.error('API POST /api/v1/hardware_requests error: %s', str(e))
            return self._json_response({
                'status': 'error',
                'message': str(e),
            }, status=500)
