from django.db import models
from django.contrib.auth.models import User
from django.core.validators import EmailValidator

class College(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=10, unique=True)
    is_active = models.BooleanField(default=False)
    
    def __str__(self):
        return self.name

class ExamSettings(models.Model):
    college = models.OneToOneField(College, on_delete=models.CASCADE)
    is_exam_active = models.BooleanField(default=False)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.college.name} - {'Active' if self.is_exam_active else 'Inactive'}"

class Student(models.Model):
    STAGE_CHOICES = [
        ('assignment', 'Assignment'),
        ('group_discussion', 'Group Discussion'),
        ('technical', 'Technical Round'),
        ('hr_round', 'HR Round'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('qualified', 'Qualified'),
        ('rejected', 'Rejected'),
    ]
    
    # Registration fields
    name = models.CharField(max_length=200, default='Unknown')
    email = models.EmailField(unique=True, validators=[EmailValidator()], default='default@example.com')
    mobile = models.CharField(max_length=10, default='0000000000')
    roll_number = models.CharField(max_length=50, default='', blank=True)
    stream = models.CharField(max_length=200, default='Not Specified')
    skills = models.TextField(blank=True, default='')
    college_name = models.CharField(max_length=300, default='Default College')
    ssc_grade = models.CharField(max_length=10, default='0.0')
    intermediate_grade = models.CharField(max_length=10, default='0.0')
    current_semester_cgpa = models.CharField(max_length=10, default='0.0', blank=True)
    
    # System fields
    password = models.CharField(max_length=12, default='temp1234')
    college = models.ForeignKey(College, on_delete=models.CASCADE, null=True, blank=True)
    current_stage = models.CharField(max_length=20, choices=STAGE_CHOICES, default='assignment')
    assignment_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    group_discussion_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    technical_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    hr_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    registration_time = models.DateTimeField(auto_now_add=True)
    login_time = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.name} ({self.email})"

class Assignment(models.Model):
    student = models.OneToOneField(Student, on_delete=models.CASCADE)
    submission_time = models.DateTimeField(auto_now=True)
    
    # Individual section scores
    aiml_score = models.IntegerField(default=0, help_text="AI/ML Score (out of 30 marks)")
    fullstack_score = models.IntegerField(default=0, help_text="Full Stack Score (out of 30 marks)")
    logic_score = models.IntegerField(default=0, help_text="Logic & Reasoning Score (out of 40 marks)")
    programming_score = models.IntegerField(default=0, help_text="Programming Score (out of 100 marks)")
    
    # Overall scores
    total_score = models.IntegerField(default=0, help_text="Total Score (out of 200 marks)")
    is_passed = models.BooleanField(default=False, help_text="Qualified for next round (≥160/200)")
    
    def calculate_final_score(self):
        # Direct sum: AI/ML(30) + FullStack(30) + Logic(40) + Programming(100) = 200 total
        self.total_score = self.aiml_score + self.fullstack_score + self.logic_score + self.programming_score
        
        # Qualification criteria: 160+ out of 200 (80%)
        self.is_passed = self.total_score >= 160
        
        # Set status to completed - admin will approve/reject later
        self.student.assignment_status = 'completed'
        
        self.student.save()
        return self.total_score
    
    def __str__(self):
        return f"{self.student.name} - {self.total_score}/200 ({'QUALIFIED' if self.is_passed else 'REJECTED'})"

class MCQAnswer(models.Model):
    SECTION_CHOICES = [
        ('homepage', 'AI/ML Questions'),
        ('coding-theory', 'Full Stack Questions'),
        ('logic-reasoning', 'Logic & Reasoning Questions'),
    ]
    
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE)
    section = models.CharField(max_length=20, choices=SECTION_CHOICES)
    question = models.CharField(max_length=10)
    answer = models.CharField(max_length=200)
    is_correct = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.assignment.student.name} - {self.section} - {self.question}"

class ProgrammingTask(models.Model):
    LANGUAGE_CHOICES = [
        ('javascript', 'JavaScript'),
        ('python', 'Python'),
        ('java', 'Java'),
        ('cpp', 'C++'),
        ('c', 'C'),
        ('csharp', 'C#'),
        ('php', 'PHP'),
        ('ruby', 'Ruby'),
    ]
    
    assignment = models.OneToOneField(Assignment, on_delete=models.CASCADE)
    language = models.CharField(max_length=20, choices=LANGUAGE_CHOICES)
    code = models.TextField()
    test_passed = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.assignment.student.name} - {self.language}"

class CodeSubmission(models.Model):
    PROBLEM_CHOICES = [
        ('leap', 'Leap Year Checker'),
        ('nextprime', 'Next Prime Finder'),
        ('hcf', 'HCF of Two Numbers'),
        ('median', 'Median of Two Lists'),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    problem = models.CharField(max_length=20, choices=PROBLEM_CHOICES)
    code = models.TextField()
    result = models.TextField()
    score = models.IntegerField(default=0)
    submitted_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.student.name} - {self.problem} - {self.score} marks"

class GroupDiscussion(models.Model):
    student = models.OneToOneField(Student, on_delete=models.CASCADE)
    assignment_score = models.IntegerField(default=0, help_text="Assignment Score from previous round")
    gd_score = models.IntegerField(default=0, help_text="Group Discussion Score (0-100, manually entered by admin)")
    total_score = models.IntegerField(default=0, help_text="Total Score (Assignment + GD)")
    status = models.CharField(max_length=20, default='pending', choices=[
        ('pending', 'Pending'),
        ('selected', 'Selected'),
        ('rejected', 'Rejected')
    ])
    created_at = models.DateTimeField(auto_now_add=True)
    
    def calculate_total_score(self):
        self.total_score = self.assignment_score + self.gd_score
        return self.total_score
    
    def __str__(self):
        return f"{self.student.name} - GD ({self.status}) - {self.total_score}"

class TechnicalRound(models.Model):
    student = models.OneToOneField(Student, on_delete=models.CASCADE)
    assignment_score = models.IntegerField(default=0, help_text="Assignment Score")
    gd_score = models.IntegerField(default=0, help_text="Group Discussion Score from previous round")
    technical_score = models.IntegerField(default=0, help_text="Technical Round Score (0-100, manually entered by admin)")
    total_score = models.IntegerField(default=0, help_text="Total Score (Assignment + GD + Technical)")
    status = models.CharField(max_length=20, default='pending', choices=[
        ('pending', 'Pending'),
        ('selected', 'Selected'),
        ('rejected', 'Rejected')
    ])
    created_at = models.DateTimeField(auto_now_add=True)
    
    def calculate_total_score(self):
        self.total_score = self.assignment_score + self.gd_score + self.technical_score
        return self.total_score
    
    def __str__(self):
        return f"{self.student.name} - Technical ({self.status}) - {self.total_score}"

class HRRound(models.Model):
    student = models.OneToOneField(Student, on_delete=models.CASCADE)
    assignment_score = models.IntegerField(default=0, help_text="Assignment Score")
    gd_score = models.IntegerField(default=0, help_text="Group Discussion Score")
    technical_score = models.IntegerField(default=0, help_text="Technical Round Score")
    hr_score = models.IntegerField(default=0, help_text="HR Round Score (0-100, manually entered by admin)")
    total_score = models.IntegerField(default=0, help_text="Total Score (Assignment + GD + Technical + HR)")
    status = models.CharField(max_length=20, default='pending', choices=[
        ('pending', 'Pending'),
        ('selected', 'Selected'),
        ('rejected', 'Rejected')
    ])
    created_at = models.DateTimeField(auto_now_add=True)
    
    def calculate_total_score(self):
        self.total_score = self.assignment_score + self.gd_score + self.technical_score + self.hr_score
        return self.total_score
    
    def __str__(self):
        return f"{self.student.name} - HR ({self.status}) - {self.total_score}"

class Evaluation(models.Model):
    student = models.OneToOneField(Student, on_delete=models.CASCADE)
    
    # Programming task score (0-100)
    programming_score = models.IntegerField(default=0, help_text="Programming Task Score (0-100)")
    
    # Interview round scores (0-100)
    gd_score = models.IntegerField(default=0, help_text="Group Discussion Score (0-100)")
    technical_score = models.IntegerField(default=0, help_text="Technical Round Score (0-100)")
    hr_score = models.IntegerField(default=0, help_text="HR Round Score (0-100)")
    
    # Final weighted score calculation
    final_weighted_score = models.FloatField(default=0.0, editable=False)
    
    # Status based on final score
    status = models.CharField(max_length=10, default='Fail', editable=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        # Calculate final weighted score including programming task
        total_scores = [self.programming_score, self.gd_score, self.technical_score, self.hr_score]
        non_zero_scores = [score for score in total_scores if score > 0]
        self.final_weighted_score = sum(non_zero_scores) / len(non_zero_scores) if non_zero_scores else 0
        
        # Determine status
        self.status = 'Pass' if self.final_weighted_score >= 50 else 'Fail'
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.student.name} - {self.final_weighted_score:.1f}% ({self.status})"
    
    class Meta:
        verbose_name = "Evaluation"
        verbose_name_plural = "Evaluations"