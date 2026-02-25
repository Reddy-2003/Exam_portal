from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_student, name='register_student'),
    path('login/', views.login_user, name='login_user'),
    path('student-status/', views.get_student_status, name='student_status'),
    path('exam-status/', views.get_exam_status, name='exam_status'),
    path('submit/', views.submit_assignment, name='submit_assignment'),
    path('test-code/', views.test_code, name='test_code'),
    path('run-code/', views.run_code, name='run_code'),
    path('submit-code/', views.submit_code, name='submit_code'),
]
