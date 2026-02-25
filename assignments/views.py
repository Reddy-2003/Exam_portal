from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
import json
from .models import Student, Assignment, MCQAnswer, ProgrammingTask, College, ExamSettings, CodeSubmission, Evaluation
import subprocess
import tempfile
import os
try:
    from code_executor import CodeExecutor
except ImportError:
    CodeExecutor = None

@csrf_exempt
@require_http_methods(["POST"])
def register_student(request):
    try:
        data = json.loads(request.body)
        
        # Check if email already exists
        if Student.objects.filter(email=data['email']).exists():
            return JsonResponse({
                'success': False,
                'message': 'Email already registered. Please use a different email.'
            })
        
        # Get or create college from registration
        college_name = data.get('college_name', data.get('college', 'Unknown College'))
        college, created = College.objects.get_or_create(
            name=college_name,
            defaults={'code': college_name[:10].upper(), 'is_active': True}
        )
        
        # Create exam settings for new college
        if created:
            ExamSettings.objects.get_or_create(
                college=college,
                defaults={'is_exam_active': False}
            )
        
        # Create student
        student = Student.objects.create(
            name=data['name'],
            email=data['email'],
            mobile=data['mobile'],
            roll_number=data.get('roll_number', ''),
            stream=data.get('stream', 'Not Specified'),
            skills=data.get('skills', ''),
            college_name=college_name,
            ssc_grade=str(data['ssc_grade']),
            intermediate_grade=str(data['intermediate_grade']),
            current_semester_cgpa=str(data.get('current_semester_cgpa', '0.0')),
            password=data['password'],
            college=college
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Registration successful'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)

@csrf_exempt
@require_http_methods(["POST"])
def login_user(request):
    try:
        data = json.loads(request.body)
        email = data.get('email')
        password = data.get('password')
        
        try:
            student = Student.objects.get(email=email, password=password)
            return JsonResponse({
                'success': True, 
                'message': 'Login successful',
                'student_id': student.id
            })
        except Student.DoesNotExist:
            return JsonResponse({
                'success': False, 
                'message': 'Invalid email or password'
            })
            
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)

@csrf_exempt
@require_http_methods(["POST"])
def get_student_status(request):
    try:
        data = json.loads(request.body)
        email = data.get('email')
        
        student = Student.objects.get(email=email)
        return JsonResponse({
            'success': True,
            'assignment_status': student.assignment_status,
            'group_discussion_status': student.group_discussion_status,
            'technical_status': student.technical_status,
            'hr_status': student.hr_status,
            'current_stage': student.current_stage
        })
        
    except Student.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Student not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)

@csrf_exempt
@require_http_methods(["POST"])
def get_exam_status(request):
    try:
        data = json.loads(request.body)
        email = data.get('email')
        
        if email:
            student = Student.objects.get(email=email)
            
            # Check if student has failed - permanently block access
            if student.assignment_status == 'rejected':
                return JsonResponse({
                    'is_active': False,
                    'message': 'Exam access denied. Student failed and cannot retake.'
                })
            
            # Check if exam is active for student's college
            exam_settings = ExamSettings.objects.filter(
                college=student.college, 
                is_exam_active=True
            ).first()
            
            if exam_settings:
                return JsonResponse({
                    'is_active': True,
                    'message': f'Exam is active for {student.college.name}'
                })
            else:
                return JsonResponse({
                    'is_active': False,
                    'message': f'Exam not activated for {student.college.name}'
                })
        else:
            return JsonResponse({
                'is_active': False,
                'message': 'No student email provided'
            })
            
    except Student.DoesNotExist:
        return JsonResponse({
            'is_active': False,
            'message': 'Student not found'
        })
    except Exception as e:
        return JsonResponse({
            'is_active': False,
            'message': f'Error: {str(e)}'
        })

@csrf_exempt
@require_http_methods(["POST"])
def submit_assignment(request):
    try:
        data = json.loads(request.body)
        
        # Get student by email
        student_email = data.get('student')
        if not student_email:
            return JsonResponse({'success': False, 'message': 'Student email not provided'})
            
        try:
            student = Student.objects.get(email=student_email)
        except Student.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Student not found'})
        

        
        # Calculate individual section scores based on correct answers
        correct_answers = {
            'homepage': {
                'q1': 'Naive Bayes', 'q2': 'Reduction in entropy', 'q3': 'Curse of dimensionality',
                'q4': 'F1-score', 'q5': 'Both a & c', 'q6': 'Reward', 'q7': 'Prevent exploding gradients',
                'q8': 'DBSCAN', 'q9': 'RNN', 'q10': 'Dimensionality reduction', 'q11': 'Bootstrapped data sample',
                'q12': 'Sparse models', 'q13': 'Random Forest', 'q14': 'True Positive Rate vs False Positive Rate',
                'q15': 'Variance'
            },
            'coding-theory': {
                'ct1': 'useEffect', 'ct2': '401', 'ct3': 'Document Store', 'ct4': 'fs', 'ct5': 'SELECT DISTINCT',
                'ct6': 'PUSH', 'ct7': 'REST API and backend routing', 'ct8': '27017', 'ct9': 'z-index',
                'ct10': 'a & c', 'ct11': 'npm init', 'ct12': 'Key referencing another table\'s primary key',
                'ct13': 'Context API', 'ct14': 'Angular', 'ct15': 'Stateless'
            },
            'logic-reasoning': {
                'lr1': '6 days', 'lr2': '30', 'lr3': '1000', 'lr4': '144', 'lr5': '12:16',
                'lr6': '3', 'lr7': '2 hr', 'lr8': '144', 'lr9': '6 days', 'lr10': '3 km/h',
                'lr11': '24', 'lr12': '8', 'lr13': '112', 'lr14': '5/3', 'lr15': '18,000',
                'lr16': '243', 'lr17': '8:15', 'lr18': 'Chair', 'lr19': 'Three intersecting circles',
                'lr20': 'All of these'
            }
        }
        
        # Calculate scores for each section
        aiml_score = 0
        fullstack_score = 0
        logic_score = 0
        programming_score = 0
        
        # AI/ML Score: 15 questions × 2 marks = 30 marks
        if 'homepage' in data['results'] and 'answers' in data['results']['homepage']:
            answers = data['results']['homepage']['answers']
            correct_count = sum(1 for q, ans in answers.items() if correct_answers['homepage'].get(q) == ans)
            aiml_score = correct_count * 2  # 2 marks per correct answer
        
        # Full Stack Score: 15 questions × 2 marks = 30 marks
        if 'coding-theory' in data['results'] and 'answers' in data['results']['coding-theory']:
            answers = data['results']['coding-theory']['answers']
            correct_count = sum(1 for q, ans in answers.items() if correct_answers['coding-theory'].get(q) == ans)
            fullstack_score = correct_count * 2  # 2 marks per correct answer
        
        # Logic & Reasoning Score: 20 questions × 2 marks = 40 marks
        if 'logic-reasoning' in data['results'] and 'answers' in data['results']['logic-reasoning']:
            answers = data['results']['logic-reasoning']['answers']
            correct_count = sum(1 for q, ans in answers.items() if correct_answers['logic-reasoning'].get(q) == ans)
            logic_score = correct_count * 2  # 2 marks per correct answer
        
        # Programming Score: Total 100 marks (10+20+20+50)
        if 'programming-task' in data['results']:
            prog_data = data['results']['programming-task']
            if isinstance(prog_data.get('score'), dict):
                programming_score = prog_data['score'].get('percentage', 0)
            else:
                programming_score = prog_data.get('score', 0)
            
            # Ensure programming score is within valid range (0-100)
            programming_score = max(0, min(100, int(programming_score)))
        
        # Create or update assignment
        assignment, created = Assignment.objects.get_or_create(
            student=student,
            defaults={
                'aiml_score': aiml_score,
                'fullstack_score': fullstack_score,
                'logic_score': logic_score,
                'programming_score': programming_score
            }
        )
        if not created:
            assignment.aiml_score = aiml_score
            assignment.fullstack_score = fullstack_score
            assignment.logic_score = logic_score
            assignment.programming_score = programming_score
        
        # Calculate final score and pass/fail status
        final_score = assignment.calculate_final_score()
        assignment.save()
        
        # Update student status to completed (awaiting admin review)
        student.assignment_status = 'completed'
        student.save()
        
        # Refresh student data
        student.refresh_from_db()
        
        # Save MCQ answers with correct/incorrect marking
        
        for section, section_data in data['results'].items():
            if section in ['homepage', 'coding-theory', 'logic-reasoning'] and 'answers' in section_data:
                MCQAnswer.objects.filter(assignment=assignment, section=section).delete()
                
                for question, answer in section_data['answers'].items():
                    is_correct = correct_answers.get(section, {}).get(question) == answer
                    MCQAnswer.objects.create(
                        assignment=assignment,
                        section=section,
                        question=question,
                        answer=answer,
                        is_correct=is_correct
                    )
        
        # Save programming task details
        if 'programming-task' in data['results']:
            prog_data = data['results']['programming-task']
            ProgrammingTask.objects.update_or_create(
                assignment=assignment,
                defaults={
                    'language': prog_data.get('language', 'python'),
                    'code': prog_data.get('code', ''),
                    'test_passed': programming_score >= 50
                }
            )
        
        # Send email notification
        send_stage_completion_email(student, 'Assignment')
        
        return JsonResponse({
            'success': True, 
            'message': 'Assignment submitted successfully',
            'total_score': assignment.total_score,
            'qualification_status': 'QUALIFIED' if assignment.is_passed else 'REJECTED',
            'student_status': student.assignment_status,
            'current_stage': student.current_stage
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)

@csrf_exempt
@require_http_methods(["POST"])
def test_code(request):
    try:
        data = json.loads(request.body)
        code = data.get('code', '')
        language = data.get('language', 'python')
        
        executor = CodeExecutor()
        result = executor.execute_code(code, language)
        
        return JsonResponse(result)
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)

def send_stage_completion_email(student, stage):
    try:
        subject = f'Interview Stage Completed - {stage}'
        message = f'''
Dear {student.name},

Congratulations! You have successfully completed the {stage} stage of your interview process.

Your Details:
- Name: {student.name}
- Email: {student.email}
- College: {student.college_name}
- Stage Completed: {stage}

Next Steps:
Please wait for further instructions regarding the next stage of the interview process.

Best regards,
Lakkshions IT Team
'''
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [student.email],
            fail_silently=True,
        )
        
        # Also send to admin
        admin_message = f'''
Student {student.name} ({student.email}) has completed the {stage} stage.

Student Details:
- College: {student.college_name}
- Stream: {student.stream}
- Mobile: {student.mobile}
'''
        
        send_mail(
            f'Student Completed {stage} - {student.name}',
            admin_message,
            settings.DEFAULT_FROM_EMAIL,
            ['admin@company.com'],  # Replace with actual admin email
            fail_silently=True,
        )
        
    except Exception as e:
        print(f'Email sending failed: {str(e)}')

# Test cases for coding problems
TEST_CASES = {
    'leap': {
        'public': [
            {'input': '2020', 'output': 'Yes'},
            {'input': '1900', 'output': 'No'}
        ],
        'private': [
            {'input': '2000', 'output': 'Yes'},
            {'input': '1700', 'output': 'No'}
        ]
    },
    'nextprime': {
        'public': [
            {'input': '14', 'output': '17'},
            {'input': '29', 'output': '31'}
        ],
        'private': [
            {'input': '10', 'output': '11'},
            {'input': '50', 'output': '53'}
        ]
    },
    'hcf': {
        'public': [
            {'input': '12\n18', 'output': '6'},
            {'input': '60\n48', 'output': '12'}
        ],
        'private': [
            {'input': '15\n25', 'output': '5'},
            {'input': '100\n75', 'output': '25'}
        ]
    },
    'median': {
        'public': [
            {'input': '1 3 5\n2 4 6', 'output': '3.5'},
            {'input': '1 2\n3 4 5', 'output': '3'}
        ],
        'private': [
            {'input': '10 20\n15 25 35', 'output': '20'},
            {'input': '1\n2 3 4 5', 'output': '3'}
        ]
    }
}

MARKS = {
    'leap': 10,
    'nextprime': 20,
    'hcf': 20,
    'median': 50,
}

@csrf_exempt
def run_code(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            problem = data.get("problem")
            user_code = data.get("code", "")

            if not problem or problem not in TEST_CASES:
                return JsonResponse({
                    "status": "error",
                    "message": "Invalid problem selected",
                    "test_results": [],
                    "score": 0,
                    "total_score": MARKS.get(problem, 0)
                })

            if not user_code.strip():
                return JsonResponse({
                    "status": "error",
                    "message": "No code provided",
                    "test_results": [],
                    "score": 0,
                    "total_score": MARKS.get(problem, 0)
                })

            # Check for basic syntax errors first
            try:
                compile(user_code, '<string>', 'exec')
            except SyntaxError as e:
                return JsonResponse({
                    "status": "compile_error",
                    "message": f"Syntax Error: {str(e)}",
                    "test_results": [],
                    "score": 0,
                    "total_score": MARKS.get(problem, 0)
                })

            public_cases = TEST_CASES[problem]["public"]
            private_cases = TEST_CASES[problem]["private"]
            
            test_results = []
            passed_count = 0
            total_count = len(public_cases) + len(private_cases)

            # Run public test cases
            for i, case in enumerate(public_cases):
                result = run_single_test(user_code, case, f"Test Case {i+1}", show_details=True)
                test_results.append(result)
                if result["status"] == "passed":
                    passed_count += 1

            # Run private test cases
            for i, case in enumerate(private_cases):
                result = run_single_test(user_code, case, f"Hidden Test {i+1}", show_details=False)
                test_results.append(result)
                if result["status"] == "passed":
                    passed_count += 1

            # Calculate score
            full_marks = MARKS.get(problem, 0)
            score = int((passed_count / total_count) * full_marks) if total_count > 0 else 0

            # Determine overall status
            if passed_count == total_count:
                status = "accepted"
                message = f"All test cases passed! Perfect solution."
            elif passed_count > 0:
                status = "partial"
                message = f"Partial solution: {passed_count}/{total_count} test cases passed."
            else:
                status = "failed"
                message = "No test cases passed. Please check your logic."

            return JsonResponse({
                "status": status,
                "message": message,
                "test_results": test_results,
                "score": score,
                "total_score": full_marks,
                "passed_count": passed_count,
                "total_count": total_count
            })
            
        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": f"Server error: {str(e)}",
                "test_results": [],
                "score": 0,
                "total_score": MARKS.get(problem, 0) if problem else 0
            })
    


def run_single_test(user_code, test_case, test_name, show_details=True):
    """Run a single test case and return detailed results"""
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as tmp_file:
            tmp_file.write(user_code)
            tmp_file.flush()
            tmp_path = tmp_file.name

        # Run the code with timeout
        process = subprocess.run(
            ["python", tmp_path],
            input=test_case["input"],
            capture_output=True,
            timeout=5,
            text=True
        )

        # Clean up
        os.unlink(tmp_path)

        if process.returncode != 0:
            error_msg = process.stderr.strip()
            return {
                "name": test_name,
                "status": "runtime_error",
                "input": test_case["input"] if show_details else "Hidden",
                "expected": test_case["output"] if show_details else "Hidden",
                "actual": "",
                "error": error_msg if show_details else "Runtime Error",
                "execution_time": "N/A"
            }

        actual_output = process.stdout.strip()
        expected_output = test_case["output"].strip()
        
        if actual_output == expected_output:
            return {
                "name": test_name,
                "status": "passed",
                "input": test_case["input"] if show_details else "Hidden",
                "expected": expected_output if show_details else "Hidden",
                "actual": actual_output if show_details else "Hidden",
                "error": "",
                "execution_time": "< 1s"
            }
        else:
            return {
                "name": test_name,
                "status": "wrong_answer",
                "input": test_case["input"] if show_details else "Hidden",
                "expected": expected_output if show_details else "Hidden",
                "actual": actual_output if show_details else "Wrong Answer",
                "error": "",
                "execution_time": "< 1s"
            }

    except subprocess.TimeoutExpired:
        try:
            os.unlink(tmp_path)
        except:
            pass
        return {
            "name": test_name,
            "status": "timeout",
            "input": test_case["input"] if show_details else "Hidden",
            "expected": test_case["output"] if show_details else "Hidden",
            "actual": "",
            "error": "Time Limit Exceeded (>5s)",
            "execution_time": "> 5s"
        }
    except Exception as e:
        try:
            os.unlink(tmp_path)
        except:
            pass
        return {
            "name": test_name,
            "status": "error",
            "input": test_case["input"] if show_details else "Hidden",
            "expected": test_case["output"] if show_details else "Hidden",
            "actual": "",
            "error": str(e) if show_details else "System Error",
            "execution_time": "N/A"
        }

@csrf_exempt
def submit_code(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            problem = data.get("problem")
            user_code = data.get("code", "")
            result = data.get("result", "")
            score = data.get("score", 0)
            
            # Get current user from localStorage (frontend will send email)
            user_email = data.get('student_email')
            if not user_email:
                return JsonResponse({"message": "Login required", "score": 0}, status=401)
            
            try:
                student = Student.objects.get(email=user_email)
                
                # Create or update submission for this problem
                submission, created = CodeSubmission.objects.update_or_create(
                    student=student,
                    problem=problem,
                    defaults={
                        'code': user_code,
                        'result': result,
                        'score': score
                    }
                )
                
                # Update programming score in Evaluation model
                from .models import Evaluation
                evaluation, eval_created = Evaluation.objects.get_or_create(
                    student=student,
                    defaults={'programming_score': score}
                )
                
                # Update programming score (take the highest score)
                if score > evaluation.programming_score:
                    evaluation.programming_score = score
                    evaluation.save()
                
                action = "created" if created else "updated"
                return JsonResponse({
                    "message": f"Code {action} successfully! Score saved in evaluation.", 
                    "score": score,
                    "problem": problem
                })
                
            except Student.DoesNotExist:
                return JsonResponse({"message": "Student not found", "score": 0}, status=404)
                
        except json.JSONDecodeError:
            return JsonResponse({"message": "Invalid JSON data", "score": 0}, status=400)
        except Exception as e:
            return JsonResponse({"message": f"Server error: {str(e)}", "score": 0}, status=500)
    
    return JsonResponse({"message": "Invalid request method", "score": 0}, status=405)