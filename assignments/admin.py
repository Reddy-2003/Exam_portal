from django.contrib import admin
from django.http import HttpResponse
from django.utils.translation import gettext_lazy as _
import csv
from .models import Student, Assignment, MCQAnswer, ProgrammingTask, College, ExamSettings, Evaluation, CodeSubmission, GroupDiscussion, TechnicalRound, HRRound

# Custom filter for Assignment Pass/Fail status
class AssignmentPassFailFilter(admin.SimpleListFilter):
    title = _('Pass/Fail Status')
    parameter_name = 'status'

    def lookups(self, request, model_admin):
        return (
            ('pass', _('Pass')),
            ('fail', _('Fail')),
        )

    def queryset(self, request, queryset):
        if self.value() == 'pass':
            return queryset.filter(total_score__gte=160)
        if self.value() == 'fail':
            return queryset.filter(total_score__lt=160)
        return queryset

# Custom filter for Score Ordering
class ScoreOrderingFilter(admin.SimpleListFilter):
    title = _('Score Ordering')
    parameter_name = 'score_order'

    def lookups(self, request, model_admin):
        return (
            ('high_low', _('High → Low')),
            ('low_high', _('Low → High')),
        )

    def queryset(self, request, queryset):
        if self.value() == 'high_low':
            return queryset.order_by('-total_score')
        if self.value() == 'low_high':
            return queryset.order_by('total_score')
        return queryset

# Custom filter for Evaluation Pass/Fail status
class EvaluationPassFailFilter(admin.SimpleListFilter):
    title = _('Pass/Fail Status')
    parameter_name = 'status'

    def lookups(self, request, model_admin):
        return (
            ('pass', _('Pass')),
            ('fail', _('Fail')),
        )

    def queryset(self, request, queryset):
        if self.value() == 'pass':
            return queryset.filter(final_weighted_score__gte=50)
        if self.value() == 'fail':
            return queryset.filter(final_weighted_score__lt=50)
        return queryset

@admin.register(College)
class CollegeAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'code']

@admin.register(ExamSettings)
class ExamSettingsAdmin(admin.ModelAdmin):
    list_display = ['college', 'is_exam_active', 'start_time', 'end_time']
    list_filter = ['is_exam_active', 'college']
    actions = ['activate_exam', 'deactivate_exam', 'activate_all_exams']
    
    def activate_exam(self, request, queryset):
        queryset.update(is_exam_active=True)
        self.message_user(request, f'✅ Activated exam for {queryset.count()} colleges')
    activate_exam.short_description = '🟢 Activate exam for selected colleges'
    
    def deactivate_exam(self, request, queryset):
        queryset.update(is_exam_active=False)
        self.message_user(request, f'❌ Deactivated exam for {queryset.count()} colleges')
    deactivate_exam.short_description = '🔴 Deactivate exam for selected colleges'
    
    def activate_all_exams(self, request, queryset):
        # Activate all exam settings
        ExamSettings.objects.all().update(is_exam_active=True)
        self.message_user(request, '🚀 Activated exams for ALL colleges!')
    activate_all_exams.short_description = '🚀 Activate ALL college exams'

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['email', 'college', 'current_stage', 'assignment_status', 'group_discussion_status', 'technical_status', 'hr_status', 'login_time']
    list_filter = ['college', 'current_stage', 'assignment_status', 'group_discussion_status', 'technical_status', 'hr_status', 'login_time']
    search_fields = ['email', 'name']
    readonly_fields = ['login_time']
    actions = [
        'approve_assignment', 'reject_assignment',
        'approve_group_discussion', 'reject_group_discussion', 
        'approve_technical', 'reject_technical',
        'approve_hr', 'reject_hr',
        'reset_password'
    ]
    
    def approve_assignment(self, request, queryset):
        count = 0
        for student in queryset.filter(assignment_status='completed'):
            student.assignment_status = 'qualified'
            student.current_stage = 'group_discussion'
            student.group_discussion_status = 'in_progress'
            student.save()
            count += 1
        self.message_user(request, f'✅ Approved {count} students for Assignment')
    approve_assignment.short_description = '✅ Approve Assignment (Completed → Qualified)'
    
    def reject_assignment(self, request, queryset):
        count = 0
        for student in queryset.filter(assignment_status='completed'):
            student.assignment_status = 'rejected'
            student.save()
            count += 1
        self.message_user(request, f'❌ Rejected {count} students for Assignment')
    reject_assignment.short_description = '❌ Reject Assignment (Completed → Rejected)'
    
    def approve_group_discussion(self, request, queryset):
        count = 0
        for student in queryset.filter(group_discussion_status='completed'):
            student.group_discussion_status = 'qualified'
            student.current_stage = 'technical'
            student.technical_status = 'in_progress'
            student.save()
            count += 1
        self.message_user(request, f'✅ Approved {count} students for Group Discussion')
    approve_group_discussion.short_description = '✅ Approve Group Discussion'
    
    def reject_group_discussion(self, request, queryset):
        count = 0
        for student in queryset.filter(group_discussion_status='completed'):
            student.group_discussion_status = 'rejected'
            student.save()
            count += 1
        self.message_user(request, f'❌ Rejected {count} students for Group Discussion')
    reject_group_discussion.short_description = '❌ Reject Group Discussion'
    
    def approve_technical(self, request, queryset):
        count = 0
        for student in queryset.filter(technical_status='completed'):
            student.technical_status = 'qualified'
            student.current_stage = 'hr_round'
            student.hr_status = 'in_progress'
            student.save()
            count += 1
        self.message_user(request, f'✅ Approved {count} students for Technical Round')
    approve_technical.short_description = '✅ Approve Technical Round'
    
    def reject_technical(self, request, queryset):
        count = 0
        for student in queryset.filter(technical_status='completed'):
            student.technical_status = 'rejected'
            student.save()
            count += 1
        self.message_user(request, f'❌ Rejected {count} students for Technical Round')
    reject_technical.short_description = '❌ Reject Technical Round'
    
    def approve_hr(self, request, queryset):
        count = 0
        for student in queryset.filter(hr_status='completed'):
            student.hr_status = 'qualified'
            student.save()
            count += 1
        self.message_user(request, f'✅ Approved {count} students for HR Round')
    approve_hr.short_description = '✅ Approve HR Round'
    
    def reject_hr(self, request, queryset):
        count = 0
        for student in queryset.filter(hr_status='completed'):
            student.hr_status = 'rejected'
            student.save()
            count += 1
        self.message_user(request, f'❌ Rejected {count} students for HR Round')
    reject_hr.short_description = '❌ Reject HR Round'
    
    def reset_password(self, request, queryset):
        for student in queryset:
            student.password = 'newpass123'
            student.save()
        self.message_user(request, f'Reset passwords for {queryset.count()} students')
    reset_password.short_description = 'Reset selected student passwords'

@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ['get_name', 'get_email', 'get_phone', 'get_status', 'aiml_score', 'fullstack_score', 'logic_score', 'programming_score', 'total_score', 'get_score_percentage', 'submission_time']
    list_filter = [
        ScoreOrderingFilter,  # Score ordering filter
        'student__college',  # Filter by college
        AssignmentPassFailFilter,  # Custom pass/fail filter
        'submission_time',  # Filter by submission date
    ]
    ordering = ['-total_score']  # Default ordering: highest score first
    search_fields = ['student__name', 'student__email', 'student__mobile']
    readonly_fields = ['submission_time', 'total_score', 'is_passed']
    actions = ['push_to_gd', 'reject_assignment', 'export_to_excel']

    def reject_assignment(self, request, queryset):
        count = 0
        for assignment in queryset:
            student = assignment.student
            student.assignment_status = 'rejected'
            student.save()
            count += 1
        self.message_user(request, f'❌ Rejected {count} students from Assignment round')
    reject_assignment.short_description = '❌ Reject Assignment'

    def get_name(self, obj):
        return obj.student.name
    get_name.short_description = 'Name'
    
    def get_email(self, obj):
        return obj.student.email
    get_email.short_description = 'Email'
    
    def get_phone(self, obj):
        return obj.student.mobile
    get_phone.short_description = 'Phone Number'
    
    def get_status(self, obj):
        if obj.is_passed:
            return '✅ PASSED'
        else:
            return '❌ FAILED'
    get_status.short_description = 'Status'
    
    def get_score_percentage(self, obj):
        if obj.total_score > 0:
            percentage = (obj.total_score / 200) * 100
            return f"{percentage:.1f}%"
        return "0.0%"
    get_score_percentage.short_description = 'Score %'
    get_score_percentage.admin_order_field = 'total_score'
    
    def get_gk_score(self, obj):
        gk_answers = MCQAnswer.objects.filter(assignment=obj, section='homepage')
        if gk_answers.exists():
            correct = gk_answers.filter(is_correct=True).count()
            total = gk_answers.count()
            return f"{correct}/{total} ({round(correct/total*100)}%)"
        return "Not completed"
    get_gk_score.short_description = 'General Knowledge'
    
    def get_ct_score(self, obj):
        ct_answers = MCQAnswer.objects.filter(assignment=obj, section='coding-theory')
        if ct_answers.exists():
            correct = ct_answers.filter(is_correct=True).count()
            total = ct_answers.count()
            return f"{correct}/{total} ({round(correct/total*100)}%)"
        return "Not completed"
    get_ct_score.short_description = 'Coding Theory'
    
    def get_programming_language(self, obj):
        try:
            return obj.programmingtask.language
        except:
            return "Not submitted"
    get_programming_language.short_description = 'Programming Language'
    
    def export_detailed_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="detailed_student_results.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Name', 'Email', 'Phone', 'College', 'Stream', 'Skills', 
                        'AI/ML Score', 'Full Stack Score', 'Logic Score', 'Programming Score', 
                        'Final Score', 'Status', 'Submission Time'])
        
        for assignment in queryset:
            writer.writerow([
                assignment.student.name,
                assignment.student.email,
                assignment.student.mobile,
                assignment.student.college_name,
                assignment.student.stream,
                assignment.student.skills,
                f"{assignment.aiml_score}%",
                f"{assignment.fullstack_score}%",
                f"{assignment.logic_score}%",
                f"{assignment.programming_score}%",
                f"{assignment.total_score}%",
                'PASSED' if assignment.is_passed else 'FAILED',
                assignment.submission_time
            ])
        
        return response
    export_detailed_csv.short_description = "📊 Export Detailed Results to CSV"
    
    def push_to_gd(self, request, queryset):
        created_count = 0
        for assignment in queryset:
            gd, created = GroupDiscussion.objects.get_or_create(
                student=assignment.student,
                defaults={'assignment_score': assignment.total_score}
            )
            if created:
                assignment.student.assignment_status = 'qualified'
                assignment.student.group_discussion_status = 'in_progress'
                assignment.student.current_stage = 'group_discussion'
                assignment.student.save()
                created_count += 1
        
        self.message_user(request, f'✅ Pushed {created_count} students to Group Discussion')
    push_to_gd.short_description = '🚀 Push to GD'
    
    def export_to_excel(self, request, queryset):
        import pandas as pd
        from django.http import HttpResponse
        
        data = []
        for assignment in queryset:
            data.append({
                'name': assignment.student.name,
                'email': assignment.student.email,
                'aiml_score': assignment.aiml_score,
                'fullstack_score': assignment.fullstack_score,
                'logic_score': assignment.logic_score,
                'programming_score': assignment.programming_score,
                'total_score': assignment.total_score,
                'status': 'PASSED' if assignment.is_passed else 'FAILED'
            })
        
        df = pd.DataFrame(data)
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="assignments.xlsx"'
        df.to_excel(response, index=False)
        return response
    export_to_excel.short_description = '📊 Export to Excel'

@admin.register(MCQAnswer)
class MCQAnswerAdmin(admin.ModelAdmin):
    list_display = ['assignment', 'section', 'question', 'answer', 'is_correct']
    list_filter = ['section', 'is_correct']
    search_fields = ['assignment__student__email']

@admin.register(ProgrammingTask)
class ProgrammingTaskAdmin(admin.ModelAdmin):
    list_display = ['assignment', 'language', 'test_passed']
    list_filter = ['language', 'test_passed']
    search_fields = ['assignment__student__email']
    readonly_fields = ['code_preview']
    
    def code_preview(self, obj):
        return obj.code[:200] + "..." if len(obj.code) > 200 else obj.code
    code_preview.short_description = 'Code Preview'

@admin.register(GroupDiscussion)
class GroupDiscussionAdmin(admin.ModelAdmin):
    list_display = ['student', 'get_email', 'assignment_score', 'gd_score', 'total_score', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['student__name', 'student__email']
    actions = ['push_to_technical', 'reject_group_discussion', 'export_to_excel']

    def reject_group_discussion(self, request, queryset):
        count = 0
        for gd in queryset:
            gd.status = 'rejected'
            gd.save()
            gd.student.group_discussion_status = 'rejected'
            gd.student.save()
            count += 1
        self.message_user(request, f'❌ Rejected {count} students from Group Discussion')
    reject_group_discussion.short_description = '❌ Reject Group Discussion'

    def save_model(self, request, obj, form, change):
        obj.calculate_total_score()
        super().save_model(request, obj, form, change)

    def get_email(self, obj):
        return obj.student.email
    get_email.short_description = 'Email'

    def push_to_technical(self, request, queryset):
        created_count = 0
        for gd in queryset.filter(status='pending'):
            gd.calculate_total_score()
            gd.save()
            tech, created = TechnicalRound.objects.get_or_create(
                student=gd.student,
                defaults={
                    'assignment_score': gd.assignment_score,
                    'gd_score': gd.gd_score
                }
            )
            if created:
                gd.student.group_discussion_status = 'qualified'
                gd.student.technical_status = 'in_progress'
                gd.student.current_stage = 'technical'
                gd.student.save()
                gd.status = 'selected'
                gd.save()
                created_count += 1
        
        self.message_user(request, f'✅ Pushed {created_count} students to Technical Round')
    push_to_technical.short_description = '🚀 Push to Technical'
    
    def export_to_excel(self, request, queryset):
        import pandas as pd
        from django.http import HttpResponse
        
        data = []
        for gd in queryset:
            data.append({
                'name': gd.student.name,
                'email': gd.student.email,
                'assignment_score': gd.assignment_score,
                'gd_score': gd.gd_score,
                'total_score': gd.total_score,
                'status': gd.status,
                'created_at': gd.created_at.replace(tzinfo=None)
            })
        
        df = pd.DataFrame(data)
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="group_discussion.xlsx"'
        df.to_excel(response, index=False)
        return response
    export_to_excel.short_description = '📊 Export to Excel'

@admin.register(TechnicalRound)
class TechnicalRoundAdmin(admin.ModelAdmin):
    list_display = ['student', 'get_email', 'assignment_score', 'gd_score', 'technical_score', 'total_score', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['student__name', 'student__email']
    actions = ['push_to_hr', 'reject_technical', 'export_to_excel']

    def reject_technical(self, request, queryset):
        count = 0
        for tech in queryset:
            tech.status = 'rejected'
            tech.save()
            tech.student.technical_status = 'rejected'
            tech.student.save()
            count += 1
        self.message_user(request, f'❌ Rejected {count} students from Technical Round')
    reject_technical.short_description = '❌ Reject Technical Round'

    def save_model(self, request, obj, form, change):
        obj.calculate_total_score()
        super().save_model(request, obj, form, change)

    def get_email(self, obj):
        return obj.student.email
    get_email.short_description = 'Email'

    def push_to_hr(self, request, queryset):
        created_count = 0
        for tech in queryset.filter(status='pending'):
            tech.calculate_total_score()
            tech.save()
            hr, created = HRRound.objects.get_or_create(
                student=tech.student,
                defaults={
                    'assignment_score': tech.assignment_score,
                    'gd_score': tech.gd_score,
                    'technical_score': tech.technical_score
                }
            )
            if created:
                tech.student.technical_status = 'qualified'
                tech.student.hr_status = 'in_progress'
                tech.student.current_stage = 'hr_round'
                tech.student.save()
                tech.status = 'selected'
                tech.save()
                created_count += 1
        
        self.message_user(request, f'✅ Pushed {created_count} students to HR Round')
    push_to_hr.short_description = '🚀 Push to HR'
    
    def export_to_excel(self, request, queryset):
        import pandas as pd
        from django.http import HttpResponse
        
        data = []
        for tech in queryset:
            data.append({
                'name': tech.student.name,
                'email': tech.student.email,
                'assignment_score': tech.assignment_score,
                'gd_score': tech.gd_score,
                'technical_score': tech.technical_score,
                'total_score': tech.total_score,
                'status': tech.status,
                'created_at': tech.created_at.replace(tzinfo=None)
            })
        
        df = pd.DataFrame(data)
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="technical_round.xlsx"'
        df.to_excel(response, index=False)
        return response
    export_to_excel.short_description = '📊 Export to Excel'

@admin.register(HRRound)
class HRRoundAdmin(admin.ModelAdmin):
    list_display = ['student', 'get_email', 'assignment_score', 'gd_score', 'technical_score', 'hr_score', 'total_score', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['student__name', 'student__email']
    actions = ['mark_selected', 'reject_hr', 'export_to_excel']

    def reject_hr(self, request, queryset):
        count = 0
        for hr in queryset:
            hr.status = 'rejected'
            hr.save()
            hr.student.hr_status = 'rejected'
            hr.student.save()
            count += 1
        self.message_user(request, f'❌ Rejected {count} students from HR Round')
    reject_hr.short_description = '❌ Reject HR Round'

    def save_model(self, request, obj, form, change):
        obj.calculate_total_score()
        super().save_model(request, obj, form, change)

    def get_email(self, obj):
        return obj.student.email
    get_email.short_description = 'Email'

    def mark_selected(self, request, queryset):
        selected_count = 0
        for hr in queryset.filter(status='pending'):
            hr.calculate_total_score()
            hr.student.hr_status = 'qualified'
            hr.student.save()
            hr.status = 'selected'
            hr.save()
            selected_count += 1
        
        self.message_user(request, f'✅ Marked {selected_count} students as Selected (Finalized)')
    mark_selected.short_description = '🏆 Mark Selected (Finalize)'
    
    def export_to_excel(self, request, queryset):
        import pandas as pd
        from django.http import HttpResponse
        
        data = []
        for hr in queryset:
            data.append({
                'name': hr.student.name,
                'email': hr.student.email,
                'assignment_score': hr.assignment_score,
                'gd_score': hr.gd_score,
                'technical_score': hr.technical_score,
                'hr_score': hr.hr_score,
                'total_score': hr.total_score,
                'status': hr.status,
                'created_at': hr.created_at.replace(tzinfo=None)
            })
        
        df = pd.DataFrame(data)
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="hr_round.xlsx"'
        df.to_excel(response, index=False)
        return response
    export_to_excel.short_description = '📊 Export to Excel'

@admin.register(Evaluation)
class EvaluationAdmin(admin.ModelAdmin):
    list_display = (
        'student', 
        'get_email', 
        'get_phone_number', 
        'gd_score', 
        'technical_score', 
        'hr_score',
        'final_weighted_score', 
        'status'
    )
    
    list_filter = (
        'gd_score', 
        'technical_score', 
        'hr_score', 
        EvaluationPassFailFilter,
        'created_at',
    )
    
    search_fields = ('student__name', 'student__email')
    readonly_fields = ('final_weighted_score', 'status', 'created_at', 'updated_at')
    
    fields = (
        'student',
        ('gd_score', 'technical_score', 'hr_score'),
        ('final_weighted_score', 'status'),
        ('created_at', 'updated_at')
    )
    
    def get_email(self, obj):
        return obj.student.email
    get_email.short_description = 'Email'
    
    def get_phone_number(self, obj):
        return obj.student.mobile
    get_phone_number.short_description = 'Phone Number'

@admin.register(CodeSubmission)
class CodeSubmissionAdmin(admin.ModelAdmin):
    list_display = ('student', 'problem', 'score', 'submitted_at')
    list_filter = ('problem', 'submitted_at')
    search_fields = ('student__name', 'student__email', 'problem')
    readonly_fields = ('submitted_at',)

admin.site.site_header = "Interview Platform Admin"
admin.site.site_title = "Interview Admin"
admin.site.index_title = "Welcome to Interview Platform Administration"