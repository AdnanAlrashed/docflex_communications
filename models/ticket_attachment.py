from odoo import models, fields, api, _
from odoo.exceptions import UserError


class DoflexTicket(models.Model):
    _inherit = 'docflex.ticket'

    attachment_number = fields.Integer(string="Attachment Number", compute='_compute_attachments')

    attachment_ids = fields.Many2many(
        'ir.attachment',
        string='المرفقات',
        relation='docflex_ticket_attachment_rel',
        column1='docflex_ticket_id',
        column2='attachment_id',
        help='الملفات المرفقة مع التذكرة'
    )

    documents_folder_id = fields.Many2one(
        'documents.document',
        string='مجلد المستندات',
        domain=[('type', '=', 'folder')],
        help='المجلد المخصص لحفظ مرفقات هذه التذكرة'
    )

    document_count = fields.Integer(
        string='عدد المستندات',
        compute='_compute_document_count',
    )

    @api.depends('attachment_ids')
    def _compute_attachments(self):
        for ticket in self:
            ticket.attachment_number = len(ticket.attachment_ids)

    def _compute_document_count(self):
        for ticket in self:
            ticket.document_count = self.env['documents.document'].sudo().search_count([
                ('res_model', '=', 'docflex.ticket'),
                ('res_id', '=', ticket.id)
            ])

    def _get_or_create_documents_folder(self, name):
        Document = self.env['documents.document'].sudo()
        parent_folder = Document.search([('name', '=', 'Docflex_Tickets'), ('type', '=', 'folder')], limit=1)
        if not parent_folder:
            parent_folder = Document.create({
                'name': 'Docflex_Tickets',
                'type': 'folder',
                'owner_id': self.env.user.id,
                'company_id': self.env.company.id,
            })
        return Document.create({
            'name': name,
            'type': 'folder',
            'folder_id': parent_folder.id,
            'owner_id': self.env.user.id,
            'company_id': self.env.company.id,
        })

    def _sync_documents(self):
        Document = self.env['documents.document'].sudo()
        Attachment = self.env['ir.attachment'].sudo()

        for ticket in self:
            # نأخذ جميع المرفقات المرتبطة سواء من Many2many أو مباشرة عبر res_model/res_id
            attachments = Attachment.search([
                '|',
                ('id', 'in', ticket.attachment_ids.ids),
                '&',
                ('res_model', '=', 'docflex.ticket'),
                ('res_id', '=', ticket.id)
            ])

            for attachment in attachments:
                if not Document.search([('attachment_id', '=', attachment.id), ('res_model', '=', 'docflex.ticket'), ('res_id', '=', ticket.id)], limit=1):
                    Document.create({
                        'name': attachment.name,
                        'attachment_id': attachment.id,
                        'folder_id': ticket.documents_folder_id.id,
                        'owner_id': ticket.env.user.id,
                        'res_model': 'docflex.ticket',
                        'res_id': ticket.id,
                        'company_id': ticket.company_id.id,
                        'access_internal': 'edit',
                        'access_via_link': 'view',
                    })


    @api.model
    def create(self, vals):
        if not vals.get('documents_folder_id'):
            folder_name = f"مرفقات التذكرة {vals.get('name', 'جديد')}"
            folder = self._get_or_create_documents_folder(folder_name)
            vals['documents_folder_id'] = folder.id
        record = super().create(vals)
        record._sync_documents()
        return record

    def write(self, vals):
        res = super().write(vals)
        for ticket in self:
            if not ticket.documents_folder_id:
                folder_name = f"مرفقات التذكرة {ticket.name or 'جديد'}"
                ticket.documents_folder_id = self._get_or_create_documents_folder(folder_name)
        self._sync_documents()
        return res

    def open_attachments(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'مرفقات التذكرة',
            'res_model': 'ir.attachment',
            'view_mode': 'kanban,list,form',
            'domain': [('res_model', '=', 'docflex.ticket'), ('res_id', '=', self.id)],
            'context': {
                'default_res_model': 'docflex.ticket',
                'default_res_id': self.id,
            },
            'target': 'new',
        }

    def action_force_sync_documents(self):
        for ticket in self:
            if not ticket.documents_folder_id:
                folder_name = f"مرفقات التذكرة {ticket.name or 'جديد'}"
                ticket.documents_folder_id = self._get_or_create_documents_folder(folder_name)

        self._sync_documents()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Documents Synced',
            'res_model': 'documents.document',
            'view_mode': 'kanban,list,form',
            'domain': [('res_model', '=', 'docflex.ticket'), ('res_id', 'in', self.ids)],
        }
