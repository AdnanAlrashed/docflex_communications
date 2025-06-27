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


    def get_department_hierarchy(self):
        if not self:
            return {}

        hierarchy = {
            'parent': {
                'id': self.parent_id.id,
                'name': self.parent_id.name,
                # 'employees': self.parent_id.total_employee,
            } if self.parent_id else False,
            'self': {
                'id': self.id,
                'name': self.name,
                # 'employees': self.total_employee,
            },
            'children': [
                {
                    'id': child.id,
                    'name': child.name,
                    # 'employees': child.total_employee
                } for child in self.child_ids
            ]
        }

        return hierarchy
