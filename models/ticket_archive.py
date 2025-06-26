from odoo import models, fields
class DoflexTicket(models.Model):
    _inherit = 'docflex.ticket'
    
    archive_folder_id = fields.Many2one(
        'archive.folder',
        string='مجلد الأرشيف',
        tracking=True
    )
    archive_date = fields.Datetime(
        string='تاريخ الأرشفة الفعلي',
        readonly=True
    )
    archived_by = fields.Many2one(
        'res.users',
        string='مؤرشف بواسطة',
        readonly=True
    )