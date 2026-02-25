# Production Deployment Guide

## Pre-Deployment Checklist

### 1. Environment Configuration
```python
# In settings.py, update for production:
DEBUG = False
ALLOWED_HOSTS = ['your-domain.com', 'www.your-domain.com']
```

### 2. Email Configuration
```python
# Update email settings in settings.py:
EMAIL_HOST_USER = 'your-company-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-gmail-app-password'
DEFAULT_FROM_EMAIL = 'your-company-email@gmail.com'
```

### 3. Admin Email
```python
# In views.py, update admin notification email:
['admin@your-company.com']  # Line 200
```

### 4. Database Migration
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

## Production Deployment

### Option 1: Local Server
```bash
python manage.py runserver 0.0.0.0:8000
```

### Option 2: Cloud Deployment (Heroku/AWS/DigitalOcean)
1. Install gunicorn: `pip install gunicorn`
2. Create Procfile: `web: gunicorn assignment_platform.wsgi`
3. Configure static files serving
4. Set environment variables

## Security Notes
- Change SECRET_KEY for production
- Use environment variables for sensitive data
- Enable HTTPS in production
- Regular database backups recommended

## Support
For technical support, contact the development team.