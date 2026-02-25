# Interview Assessment Platform

A comprehensive Django-based interview assessment system for technical recruitment.

## Features

### Multi-Stage Assessment
- **AI/ML Questions** (15 MCQs) - 30% weight
- **Full Stack Development** (15 MCQs) - 30% weight  
- **Logic & Reasoning** (20 MCQs) - 25% weight
- **Programming Challenge** (Factorial coding) - 15% weight

### Student Management
- Online registration with detailed profiles
- Auto-generated secure passwords
- Real-time interview progress tracking
- Pass/fail determination (50% threshold)

### Admin Features
- Comprehensive student dashboard
- Detailed scoring breakdown
- Exam activation controls
- CSV export functionality
- Email notifications

## Quick Setup

### 1. Install Dependencies
```bash
pip install django django-cors-headers
```

### 2. Database Setup
```bash
python manage.py makemigrations
python manage.py migrate
```

### 3. Create Admin User
```bash
python manage.py createsuperuser
```

### 4. Run Server
```bash
python manage.py runserver
```

## Access Points

- **Student Registration**: http://localhost:8000/
- **Student Login**: http://localhost:8000/login/
- **Admin Panel**: http://localhost:8000/admin/

## System Architecture

### Models
- **Student**: Registration data, progress tracking
- **Assignment**: Detailed scoring, pass/fail status
- **College**: Institution management
- **ExamSettings**: Exam activation controls

### Assessment Flow
1. **Registration** → Auto-generated credentials
2. **Login** → Progress dashboard
3. **Assessment** → 50 questions + coding
4. **Scoring** → Weighted final score
5. **Result** → Pass (≥50%) or Fail (<50%)  

### Admin Controls
- Activate/deactivate exams per college
- Monitor student progress in real-time
- Export detailed results to CSV
- Manage interview stage progression

## Technical Stack
- **Backend**: Django 4.2.7
- **Database**: SQLite (production-ready)
- **Frontend**: HTML5, CSS3, JavaScript
- **Styling**: Modern responsive design

## Production Ready
- Secure authentication system
- Email notification integration
- Comprehensive error handling
- Scalable architecture
- Clean, maintainable codebase