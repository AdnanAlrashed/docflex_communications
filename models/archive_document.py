# ملف archive_document.py
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class ArchiveDocument(models.Model):
    _name = 'archive.document'
    _description = 'الوثيقة الأرشيفية'
    _order = 'date desc, id desc'
    
    name = fields.Char(string='اسم الوثيقة', required=True)
    reference = fields.Char(string='المرجع', required=True)
    folder_id = fields.Many2one(
        'archive.folder',
        string='مجلد الأرشيف',
        required=True,
        domain="[('active', '=', True)]"
    )
    date = fields.Date(string='تاريخ الوثيقة', default=fields.Date.today)
    description = fields.Text(string='الوصف')
    document_type = fields.Selection(
        [('incoming', 'وارد'), ('outgoing', 'صادر')],
        string='نوع الوثيقة',
        required=True
    )
    state = fields.Selection(
        [('draft', 'مسودة'), ('archived', 'مؤرشف'), ('destroyed', 'ملغى')],
        string='الحالة',
        default='draft'
    )
    ticket_id = fields.Many2one(
        'docflex.ticket',
        string='المذكرة المرتبطة',
        readonly=True
    )
    company_id = fields.Many2one(
        'res.company',
        string='الشركة',
        default=lambda self: self.env.company
    )
    archived_by = fields.Many2one(
        'res.users',
        string='مؤرشف بواسطة',
        default=lambda self: self.env.user
    )
    archive_date = fields.Datetime(
        string='تاريخ الأرشفة',
        default=fields.Datetime.now
    )
    active = fields.Boolean(default=True)
    color = fields.Integer(string='لون العلامة')

    # إضافة حقول للملحقات والصور إذا لزم الأمر
    attachment_ids = fields.Many2many(
        'ir.attachment',
        string='المرفقات'
    )
    image = fields.Binary(string='صورة الوثيقة')

    # إضافة حقول إضافية للربط مع نماذج أخرى
    partner_id = fields.Many2one(
        'res.partner',
        string='الجهة المرتبطة'
    )
    department_id = fields.Many2one(
        'hr.department',
        string='الإدارة المرتبطة'
    )

    # إضافة حقول حسابية
    folder_path = fields.Char(
        string='مسار المجلد',
        related='folder_id.complete_name',
        store=True
    )
    document_age = fields.Integer(
        string='عمر الوثيقة (أيام)',
        compute='_compute_document_age',
        store=True
    )

    @api.depends('date')
    def _compute_document_age(self):
        today = fields.Date.today()
        for doc in self:
            if doc.date:
                delta = today - doc.date
                doc.document_age = delta.days
            else:
                doc.document_age = 0

    def action_archive(self):
        for document in self:
            if document.state != 'draft':
                raise UserError(_("لا يمكن أرشفة وثيقة غير مسودة"))
            document.write({
                'state': 'archived',
                'archive_date': fields.Datetime.now(),
                'archived_by': self.env.user.id
            })

    def action_destroy(self):
        for document in self:
            if document.state != 'archived':
                raise UserError(_("لا يمكن إلغاء وثيقة غير مؤرشفة"))
            document.write({
                'state': 'destroyed',
                'active': False
            })

    def action_restore(self):
        for document in self:
            document.write({
                'state': 'draft',
                'active': True
            })

    @api.model
    def create(self, vals):
        if 'reference' not in vals:
            sequence = self.env['ir.sequence'].next_by_code('archive.document') or _('New')
            vals['reference'] = sequence
        return super().create(vals)