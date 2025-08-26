from odoo import models, fields, api
from random import randint

class ArchiveFolder(models.Model):
    _name = 'archive.folder'
    _description = 'مجلدات الأرشيف'
    _parent_name = "parent_id"
    _order = 'sequence, name'

    def _get_default_color(self):
        return randint(1, 11)
    
    name = fields.Char(string='اسم المجلد', required=True)
    parent_id = fields.Many2one(
        'archive.folder',
        string='المجلد الأب',
        index=True,
        ondelete='cascade'
    )
    child_ids = fields.One2many(
        'archive.folder',
        'parent_id',
        string='المجلدات الفرعية'
    )
    sequence = fields.Integer(string='تسلسل', default=10)
    complete_name = fields.Char(
        string='المسار الكامل',
        compute='_compute_complete_name',
        store=True
    )
    active = fields.Boolean(default=True)
    description = fields.Text(string='الوصف')
    company_id = fields.Many2one(
        'res.company',
        string='الشركة',
        default=lambda self: self.env.company
    )
    color = fields.Integer(string='اللون',default=_get_default_color)
    icon = fields.Binary(string='الأيقونة', attachment=True)

    document_ids = fields.One2many(
        'archive.document',  # النموذج المرتبط
        'folder_id',         # الحقل في النموذج المرتبط
        string='الوثائق الأرشيفية',
        domain=[('active', '=', True)]  # لعرض الوثائق النشطة فقط
    )
    
    documents_count = fields.Integer(
        string='عدد الوثائق',
        compute='_compute_documents_count',
        store=True
    )

    # مستوى العمق في الهيكل الشجري
    depth_level = fields.Integer(string='مستوى العمق', compute='_compute_depth_level', store=True)

    # تصنيف المجلدات
    folder_type = fields.Selection([
        ('department', 'إدارة'),
        ('year', 'سنة'),
        ('subject', 'موضوع'),
        ('project', 'مشروع')],
        string='نوع المجلد', required=True, default='subject')

    # تاريخ البدء والانتهاء للمجلدات الزمنية
    date_start = fields.Date(string='تاريخ البدء')
    date_end = fields.Date(string='تاريخ الانتهاء')

    @api.depends('parent_id')
    def _compute_depth_level(self):
        for folder in self:
            level = 0
            parent = folder.parent_id
            while parent:
                level += 1
                parent = parent.parent_id
            folder.depth_level = level
        
    @api.depends('document_ids')
    def _compute_documents_count(self):
        for folder in self:
            folder.documents_count = len(folder.document_ids)
    
    @api.depends('name', 'parent_id.complete_name')
    def _compute_complete_name(self):
        for folder in self:
            if folder.parent_id:
                folder.complete_name = '%s / %s' % (folder.parent_id.complete_name, folder.name)
            else:
                folder.complete_name = folder.name


    @api.model
    def get_folder_tree(self, parent_id=None):
        """ استرجاع الهيكل الشجري بكفاءة """
        domains = []
        if parent_id:
            domains.append(('parent_id', '=', parent_id))
        else:
            domains.append(('parent_id', '=', False))
        
        folders = self.search_read(
            domain=domains,
            fields=['id', 'name', 'folder_type', 'color', 'documents_count', 'child_ids'],
            order='sequence, name'
        )
        
        for folder in folders:
            folder['children'] = self.get_folder_tree(folder['id'])
            folder['icon'] = self._get_folder_icon(folder['folder_type'])
        
        return folders
