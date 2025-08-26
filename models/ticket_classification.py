from odoo import models, fields, api

class TicketClassification(models.Model):
    _name = 'ticket.classification'
    _description = 'تصنيف التذاكر'
    
    name = fields.Char(string='الاسم', required=True)
    code = fields.Char(string='الكود')
    is_default = fields.Boolean(string='افتراضي')
    active = fields.Boolean(string='نشط', default=True)