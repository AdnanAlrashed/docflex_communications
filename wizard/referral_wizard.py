from odoo import models, fields, api, _
from odoo.exceptions import UserError, AccessError
from datetime import timedelta
import logging

_logger = logging.getLogger(__name__)

class DocflexTicketReferralWizard(models.TransientModel):
    _name = 'docflex.ticket.referral.wizard'
    _description = 'معالج إحالة المذكرة'

    # إضافة حقل نوع الإجراء
    referral_type_id = fields.Many2one(
        'referral.type',
        string='نوع الإجراء',
        required=True,
        default=lambda self: self._get_default_referral_type()
    )
    
    ticket_id = fields.Many2one('docflex.ticket', string='المذكرة', required=True)
    from_user_id = fields.Many2one('res.users', string='من المستخدم', required=True)
    to_user_id = fields.Many2one('res.users', string='إلى المستخدم')
    to_department_id = fields.Many2one('hr.department', string='إلى الإدارة')
    notes = fields.Text(string='ملاحظات الإحالة')
    deadline = fields.Date(string='موعد التسليم المتوقع')
    is_urgent = fields.Boolean(string='عاجل')

    # دالة للحصول على نوع الإجراء الافتراضي
    @api.model
    def _get_default_referral_type(self):
        default_type = self.env['referral.type'].search([('is_default', '=', True)], limit=1)
        return default_type.id if default_type else False

    # عند تغيير نوع الإجراء، تحديث الموعد النهائي
    @api.onchange('referral_type_id')
    def _onchange_referral_type(self):
        if self.referral_type_id and self.referral_type_id.default_deadline_days > 0:
            self.deadline = fields.Date.today() + timedelta(days=self.referral_type_id.default_deadline_days)

    # @api.onchange('to_department_id')
    # def _onchange_to_department(self):
    #     if self.to_department_id:
    #         return {'domain': {'to_user_id': [('department_id', '=', self.to_department_id.id)]}}
    #     return {'domain': {'to_user_id': []}}

    @api.onchange('to_department_id')
    def _onchange_to_department(self):
        domain = []
        if self.to_department_id:
            # فلترة المستخدمين حسب القسم + فقط المستخدمين النشطين
            domain = [('department_id', '=', self.to_department_id.id), 
                    ('active', '=', True),
                    ('share', '=', False)]  # استبعاد المستخدمين المشتركين
        return {'domain': {'to_user_id': domain}}


    def action_refer(self):
        self.ensure_one()
        if not self.env.user.has_group('docflex_communications.group_ticket_referral'):
            raise UserError(_("ليس لديك صلاحية إحالة المذكرات. الرجاء التواصل مع المدير."))
        
        # التحقق من أن المستخدم لم يقم بإحالة المذكرة لنفسه
        if self.to_user_id and self.to_user_id.id == self.env.user.id:
            raise UserError(_("لا يمكنك إحالة المذكرة لنفسك!"))

        # التحقق من وجود إحالة سابقة لنفس المستخدم
        existing_referral = self.env['docflex.ticket.referral'].search([
            ('ticket_id', '=', self.ticket_id.id),
            ('from_user_id', '=', self.env.user.id),
            ('to_user_id', '=', self.to_user_id.id if self.to_user_id else False),
            ('to_department_id', '=', self.to_department_id.id if self.to_department_id else False),
            ('state', 'in', ['pending', 'received'])
        ], limit=1)
        
        if existing_referral:
            raise UserError(_("لقد قمت بإحالة هذه المذكرة بالفعل إلى هذا المستخدم/القسم. انتظر حتى يتم الرد عليها."))
        
        # باقي التحققات الأصلية
        if not self.to_user_id and not self.to_department_id:
            raise UserError(_("يجب تحديد مستلم أو إدارة للمذكرة"))
        # التحقق من أن المستخدم المحدد ينتمي للقسم المحدد
        if self.to_department_id and self.to_user_id:
            if self.to_user_id.department_id != self.to_department_id:
                raise UserError(_("المستخدم المحدد لا ينتمي إلى القسم المختار!"))
        
        # التحقق من وجود مستلم (مستخدم أو قسم)
        if not self.to_user_id and not self.to_department_id:
            raise UserError(_("يجب تحديد مستلم أو إدارة للمذكرة"))
        
        # تحديد المستلم لاستخدامه في رسالة القفل
        recipient = self.to_user_id.name if self.to_user_id else self.to_department_id.name
        
        # إنشاء قيم الإحالة
        referral_vals = {
            'ticket_id': self.ticket_id.id,
            'referral_type_id': self.referral_type_id.id,
            'from_user_id': self.from_user_id.id,
            'to_user_id': self.to_user_id.id if self.to_user_id else False,
            'to_department_id': self.to_department_id.id if self.to_department_id else False,
            'notes': self.notes,
            'deadline': self.deadline,
            'is_urgent': self.is_urgent,
            'state': 'pending'
        }
        
        # try:
        # إنشاء سجل الإحالة
        referral = self.env['docflex.ticket.referral'].create(referral_vals)
        
        # قفل المذكرة بعد الإحالة
        self.ticket_id.write({
            'is_locked': True,
            'lock_reason': f'مقفولة بسبب الإحالة إلى {recipient}',
            'lock_date': fields.Datetime.now(),
            'locked_by': self.env.user.id
        })
        
        # إرسال إشعارات
        self._send_referral_notifications(referral)
        
        # إغلاق النافذة المنبثقة
        return {
            'type': 'ir.actions.act_window_close',
            'context': {'default_referral_id': referral.id}
        }
        # except Exception as e:
        #     _logger.error("Failed to create referral: %s", str(e))
        #     raise UserError(_("حدث خطأ أثناء إنشاء الإحالة. الرجاء المحاولة مرة أخرى."))


    def _send_referral_notifications(self, referral):
        """إرسال الإشعارات والأنشطة للمستلمين"""
        if self.to_user_id:
            # متابعة التذكرة للمستخدم المستلم
            self.ticket_id.message_subscribe(partner_ids=[self.to_user_id.partner_id.id])
            
            # إنشاء نشاط للمستخدم المستلم
            self.ticket_id.activity_schedule(
                'mail.mail_activity_data_todo',
                user_id=self.to_user_id.id,
                summary=_('إحالة مذكرة جديدة - %s') % self.referral_type_id.name,
                note=self._get_referral_message(),
                date_deadline=self.deadline
            )
        elif self.to_department_id and self.to_department_id.manager_id.user_id:
            # إرسال إشعار لمدير القسم
            manager = self.to_department_id.manager_id.user_id
            self.ticket_id.message_subscribe(partner_ids=[manager.partner_id.id])
            self.ticket_id.activity_schedule(
                'mail.mail_activity_data_todo',
                user_id=manager.id,
                summary=_('إحالة مذكرة جديدة إلى قسمك - %s') % self.referral_type_id.name,
                note=_('تم إحالة المذكرة %s إلى قسم %s') % (self.ticket_id.name, self.to_department_id.name),
                date_deadline=self.deadline
            )
        
        # تسجيل في محادثات التذكرة
        self.ticket_id.message_post(
            body=self._get_referral_message(),
            subject=_('إحالة جديدة للمذكرة %s') % self.ticket_id.name
        )

    def _get_referral_message(self):
        """إنشاء رسالة الإحالة"""
        recipient = self.to_user_id.name if self.to_user_id else self.to_department_id.name
        return _("""
        <div style='margin:10px;'>
            <h3 style='color:#875A7B;'>تم إحالة المذكرة</h3>
            <p><b>المستلم:</b> %s</p>
            <p><b>نوع الإجراء:</b> %s</p>
            <p><b>الموعد النهائي:</b> %s</p>
            <p><b>ملاحظات:</b> %s</p>
        </div>
        """) % (
            recipient,
            self.referral_type_id.name,
            self.deadline.strftime('%Y-%m-%d') if self.deadline else 'غير محدد',
            self.notes or 'لا توجد ملاحظات'
        )


    @api.onchange('to_department_id', 'to_user_id')
    def _onchange_recipient(self):
        """تحسين اختيار المستلم"""
        if self.to_department_id and self.to_user_id:
            if self.to_user_id.department_id != self.to_department_id:
                return {
                    'warning': {
                        'title': _("تحذير"),
                        'message': _("المستخدم المحدد لا ينتمي إلى القسم المختار!")
                    }
                }
    
    def _validate_referral(self):
        """تحسين التحقق من صحة البيانات"""
        if not self.to_user_id and not self.to_department_id:
            raise UserError(_("يجب تحديد مستلم أو إدارة للمذكرة"))
        
        if not self.referral_type_id:
            raise UserError(_("يجب تحديد نوع الإجراء"))
        
        if self.ticket_id.is_locked:
            raise UserError(_("لا يمكن إحالة مذكرة مقفولة"))

