from odoo import models, fields, api, _
from odoo.exceptions import UserError, AccessError
from datetime import timedelta
class ArchiveTicketWizard(models.TransientModel):
    _name = 'archive.ticket.wizard'
    _description = 'معالج أرشفة المذكرة'
    
    ticket_id = fields.Many2one(
        'docflex.ticket',
        string='المذكرة',
        required=True,
        default=lambda self: self._default_ticket_id()
    )
    folder_id = fields.Many2one(
        'archive.folder',
        string='مجلد الأرشيف',
        required=True
    )
    notes = fields.Text(string='ملاحظات الأرشفة')
    
    def _default_ticket_id(self):
        return self.env.context.get('active_id')
    
    def action_archive_ticket(self):
        self.ensure_one()
        # البحث عن مرحلة الأرشيف بدلاً من استخدام ref مباشرةً
        archived_stage = self.env['docflex.ticket.stage'].search([
            ('code', '=', 'archived')
        ], limit=1)
        
        if not archived_stage:
            raise UserError("لم يتم العثور على مرحلة الأرشيف في النظام. الرجاء التأكد من إعدادات المراحل.")
        # أرشفة المذكرة
        self.ticket_id.write({
            'archive_folder_id': self.folder_id.id,
            'archive_date': fields.Datetime.now(),
            'archived_by': self.env.user.id,
            'stage_id': archived_stage.id,
            'active': False
        })
        
        # إنشاء وثيقة أرشيفية مرتبطة بالمجلد
        archive_doc = self.env['archive.document'].create({
            'name': self.ticket_id.name,
            'reference': self.ticket_id.number,
            'folder_id': self.folder_id.id,
            'date': fields.Date.today(),
            'description': self.notes,
            'document_type': 'incoming' if self.ticket_id.ticket_type_code == 'in' else 'outgoing',
            'state': 'archived',
            'ticket_id': self.ticket_id.id,
            'partner_id': self.ticket_id.partner_from_id.id or self.ticket_id.partner_to_id.id,
            'department_id': self.ticket_id.department_id.id
        })
        
        # ربط المرفقات إذا وجدت
        if self.ticket_id.attachment_ids:
            archive_doc.attachment_ids = [(6, 0, self.ticket_id.attachment_ids.ids)]
        
        self.ticket_id.message_post(
            body=f'تم أرشفة المذكرة في مجلد الأرشيف: {self.folder_id.complete_name}'
        )
        
        return {
            'type': 'ir.actions.act_window_close'
        }