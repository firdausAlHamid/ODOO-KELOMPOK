# -*- coding: utf-8 -*-
{
    "name": "IT Hardware Request",
    "summary": "Manage employee hardware requests, approvals, and allocations.",
    "version": "19.0.1.0.0",
    "category": "Human Resources/IT",
    "author": "Your Company",
    "website": "https://yourcompany.example.com",
    "license": "LGPL-3",
    "depends": ["base", "hr", "mail", "stock"],
    "data": [
        "security/ir.model.access.csv",
        "data/sequence_data.xml",
        "views/hardware_request_views.xml"
    ],
    "installable": True,
    "application": True,
    "auto_install": False,
}
