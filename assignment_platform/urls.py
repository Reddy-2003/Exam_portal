from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('assignments/', include('assignments.urls')),
    path('coding-platform/', TemplateView.as_view(template_name='coding-platform.html'), name='coding-platform'),
    path('', TemplateView.as_view(template_name='register.html'), name='register'),
    path('register/', TemplateView.as_view(template_name='register.html'), name='register_page'),
    path('login/', TemplateView.as_view(template_name='login.html'), name='login'),
    path('dashboard/', TemplateView.as_view(template_name='dashboard.html'), name='dashboard'),
    path('homepage/', TemplateView.as_view(template_name='homepage.html'), name='homepage'),
    path('coding-theory/', TemplateView.as_view(template_name='coding-theory.html'), name='coding-theory'),
    path('logic-reasoning/', TemplateView.as_view(template_name='logic-reasoning.html'), name='logic-reasoning'),
    path('programming-task/', TemplateView.as_view(template_name='programming-task.html'), name='programming-task'),
]