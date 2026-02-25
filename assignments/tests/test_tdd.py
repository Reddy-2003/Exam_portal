"""
TDD (Test-Driven Development) Tests for Exam Portal
=====================================================
Tests are organized by unit (model, view, admin action) and each test
verifies a single, isolated behaviour.

Run:
    docker exec exam_portal python manage.py test assignments.tests.test_tdd -v 2
"""

import json
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.admin.sites import AdminSite
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import RequestFactory

from assignments.models import (
    College, ExamSettings, Student, Assignment,
    MCQAnswer, ProgrammingTask, GroupDiscussion,
    TechnicalRound, HRRound, Evaluation, CodeSubmission,
)
from assignments.admin import (
    AssignmentAdmin, GroupDiscussionAdmin,
    TechnicalRoundAdmin, HRRoundAdmin, StudentAdmin,
)


# ---------------------------------------------------------------------------
# Helpers / Fixtures
# ---------------------------------------------------------------------------

def make_college(name="Test College", code="TC001", active=True):
    college, _ = College.objects.get_or_create(
        code=code,
        defaults={"name": name, "is_active": active},
    )
    return college


def make_exam_settings(college, active=True):
    settings, _ = ExamSettings.objects.get_or_create(
        college=college,
        defaults={"is_exam_active": active},
    )
    return settings


def make_student(
    email="student@test.com",
    name="Test Student",
    password="pass1234",
    college=None,
    assignment_status="pending",
):
    if college is None:
        college = make_college()
    return Student.objects.create(
        name=name,
        email=email,
        mobile="9876543210",
        roll_number="R001",
        stream="CSE",
        skills="Python",
        college_name=college.name,
        ssc_grade="9.0",
        intermediate_grade="8.5",
        current_semester_cgpa="8.0",
        password=password,
        college=college,
        assignment_status=assignment_status,
    )


def make_assignment(student, aiml=20, fullstack=20, logic=30, prog=80):
    assignment = Assignment.objects.create(
        student=student,
        aiml_score=aiml,
        fullstack_score=fullstack,
        logic_score=logic,
        programming_score=prog,
    )
    assignment.calculate_final_score()
    assignment.save()
    return assignment


def make_request_with_messages(method="get", path="/"):
    """Return a request object with session/messages middleware attached."""
    factory = RequestFactory()
    request = getattr(factory, method)(path)
    request.session = {}
    messages = FallbackStorage(request)
    request._messages = messages
    return request


# ---------------------------------------------------------------------------
# 1. MODEL TESTS
# ---------------------------------------------------------------------------

class CollegeModelTest(TestCase):
    """TDD-1: College model basic contract"""

    def test_str_representation(self):
        college = College(name="JNTU", code="JNTU01", is_active=True)
        self.assertEqual(str(college), "JNTU")

    def test_code_is_unique(self):
        College.objects.create(name="College A", code="CA01", is_active=True)
        with self.assertRaises(Exception):
            College.objects.create(name="College B", code="CA01", is_active=True)

    def test_default_is_not_active(self):
        college = College(name="X", code="X01")
        self.assertFalse(college.is_active)


class ExamSettingsModelTest(TestCase):
    """TDD-2: ExamSettings model"""

    def setUp(self):
        self.college = make_college()

    def test_str_when_active(self):
        es = ExamSettings(college=self.college, is_exam_active=True)
        self.assertIn("Active", str(es))

    def test_str_when_inactive(self):
        es = ExamSettings(college=self.college, is_exam_active=False)
        self.assertIn("Inactive", str(es))

    def test_one_to_one_with_college(self):
        ExamSettings.objects.create(college=self.college, is_exam_active=True)
        with self.assertRaises(Exception):
            ExamSettings.objects.create(college=self.college, is_exam_active=False)


class StudentModelTest(TestCase):
    """TDD-3: Student model defaults and field constraints"""

    def setUp(self):
        self.college = make_college()

    def test_default_stage_is_assignment(self):
        s = make_student(college=self.college)
        self.assertEqual(s.current_stage, "assignment")

    def test_all_statuses_default_pending(self):
        s = make_student(college=self.college)
        self.assertEqual(s.assignment_status, "pending")
        self.assertEqual(s.group_discussion_status, "pending")
        self.assertEqual(s.technical_status, "pending")
        self.assertEqual(s.hr_status, "pending")

    def test_email_is_unique(self):
        make_student(email="dup@test.com", college=self.college)
        with self.assertRaises(Exception):
            make_student(email="dup@test.com", college=self.college)

    def test_str_contains_name_and_email(self):
        s = make_student(name="Alice", email="alice@test.com", college=self.college)
        self.assertIn("Alice", str(s))
        self.assertIn("alice@test.com", str(s))


class AssignmentModelTest(TestCase):
    """TDD-4: Assignment score calculation and qualification logic"""

    def setUp(self):
        self.student = make_student()

    def test_calculate_final_score_sums_correctly(self):
        a = Assignment(
            student=self.student,
            aiml_score=30,
            fullstack_score=30,
            logic_score=40,
            programming_score=100,
        )
        total = a.calculate_final_score()
        self.assertEqual(total, 200)

    def test_is_passed_when_score_gte_160(self):
        a = Assignment(
            student=self.student,
            aiml_score=30,
            fullstack_score=30,
            logic_score=40,
            programming_score=60,
        )
        a.calculate_final_score()
        self.assertTrue(a.is_passed)

    def test_is_not_passed_when_score_lt_160(self):
        a = Assignment(
            student=self.student,
            aiml_score=10,
            fullstack_score=10,
            logic_score=10,
            programming_score=10,
        )
        a.calculate_final_score()
        self.assertFalse(a.is_passed)

    def test_boundary_exactly_160_passes(self):
        a = Assignment(
            student=self.student,
            aiml_score=30,
            fullstack_score=30,
            logic_score=40,
            programming_score=60,
        )
        a.calculate_final_score()
        self.assertEqual(a.total_score, 160)
        self.assertTrue(a.is_passed)

    def test_student_status_set_to_completed_after_calculate(self):
        a = Assignment(student=self.student, aiml_score=20, fullstack_score=20,
                       logic_score=30, programming_score=80)
        a.calculate_final_score()
        self.student.refresh_from_db()
        self.assertEqual(self.student.assignment_status, "completed")

    def test_str_shows_qualified(self):
        a = make_assignment(self.student, aiml=30, fullstack=30, logic=40, prog=100)
        self.assertIn("QUALIFIED", str(a))

    def test_str_shows_rejected(self):
        a = make_assignment(self.student, aiml=5, fullstack=5, logic=5, prog=5)
        self.assertIn("REJECTED", str(a))


class GroupDiscussionModelTest(TestCase):
    """TDD-5: GroupDiscussion score aggregation"""

    def setUp(self):
        self.student = make_student()

    def test_calculate_total_score(self):
        gd = GroupDiscussion(student=self.student, assignment_score=150, gd_score=70)
        total = gd.calculate_total_score()
        self.assertEqual(total, 220)
        self.assertEqual(gd.total_score, 220)

    def test_default_status_pending(self):
        gd = GroupDiscussion(student=self.student)
        self.assertEqual(gd.status, "pending")


class TechnicalRoundModelTest(TestCase):
    """TDD-6: TechnicalRound score aggregation"""

    def setUp(self):
        self.student = make_student()

    def test_calculate_total_score(self):
        tr = TechnicalRound(
            student=self.student,
            assignment_score=150,
            gd_score=70,
            technical_score=80,
        )
        total = tr.calculate_total_score()
        self.assertEqual(total, 300)


class HRRoundModelTest(TestCase):
    """TDD-7: HRRound score aggregation"""

    def setUp(self):
        self.student = make_student()

    def test_calculate_total_score(self):
        hr = HRRound(
            student=self.student,
            assignment_score=150,
            gd_score=70,
            technical_score=80,
            hr_score=90,
        )
        total = hr.calculate_total_score()
        self.assertEqual(total, 390)


class EvaluationModelTest(TestCase):
    """TDD-8: Evaluation weighted score and Pass/Fail status"""

    def setUp(self):
        self.student = make_student()

    def test_pass_when_average_gte_50(self):
        ev = Evaluation.objects.create(
            student=self.student,
            gd_score=60,
            technical_score=70,
            hr_score=80,
        )
        self.assertEqual(ev.status, "Pass")

    def test_fail_when_average_lt_50(self):
        ev = Evaluation.objects.create(
            student=self.student,
            gd_score=20,
            technical_score=30,
            hr_score=40,
        )
        self.assertEqual(ev.status, "Fail")

    def test_weighted_score_ignores_zeros(self):
        # Only gd_score=60 is non-zero → avg should be 60
        ev = Evaluation.objects.create(
            student=self.student,
            gd_score=60,
            technical_score=0,
            hr_score=0,
        )
        self.assertAlmostEqual(ev.final_weighted_score, 60.0)

    def test_weighted_score_all_zeros_gives_zero(self):
        ev = Evaluation.objects.create(
            student=self.student,
            gd_score=0,
            technical_score=0,
            hr_score=0,
        )
        self.assertEqual(ev.final_weighted_score, 0.0)
        self.assertEqual(ev.status, "Fail")


# ---------------------------------------------------------------------------
# 2. VIEW / API TESTS
# ---------------------------------------------------------------------------

class RegisterStudentViewTest(TestCase):
    """TDD-9: POST /assignments/register/ endpoint"""

    def setUp(self):
        self.client = Client()
        self.url = "/assignments/register/"
        self.valid_payload = {
            "name": "John Doe",
            "email": "john@test.com",
            "mobile": "9876543210",
            "roll_number": "R100",
            "stream": "CSE",
            "skills": "Python",
            "college_name": "Test College",
            "ssc_grade": "9.0",
            "intermediate_grade": "8.5",
            "current_semester_cgpa": "8.0",
            "password": "pass1234",
        }

    def test_successful_registration_returns_success_true(self):
        resp = self.client.post(
            self.url,
            data=json.dumps(self.valid_payload),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["success"])

    def test_duplicate_email_returns_success_false(self):
        self.client.post(
            self.url,
            data=json.dumps(self.valid_payload),
            content_type="application/json",
        )
        resp = self.client.post(
            self.url,
            data=json.dumps(self.valid_payload),
            content_type="application/json",
        )
        data = resp.json()
        self.assertFalse(data["success"])
        self.assertIn("already registered", data["message"])

    def test_registration_creates_student_in_db(self):
        self.client.post(
            self.url,
            data=json.dumps(self.valid_payload),
            content_type="application/json",
        )
        self.assertTrue(Student.objects.filter(email="john@test.com").exists())

    def test_registration_creates_college_if_new(self):
        self.client.post(
            self.url,
            data=json.dumps(self.valid_payload),
            content_type="application/json",
        )
        self.assertTrue(College.objects.filter(name="Test College").exists())

    def test_registration_creates_exam_settings_for_new_college(self):
        self.client.post(
            self.url,
            data=json.dumps(self.valid_payload),
            content_type="application/json",
        )
        college = College.objects.get(name="Test College")
        self.assertTrue(ExamSettings.objects.filter(college=college).exists())

    def test_missing_required_field_returns_400_or_failure(self):
        bad_payload = dict(self.valid_payload)
        del bad_payload["email"]
        resp = self.client.post(
            self.url,
            data=json.dumps(bad_payload),
            content_type="application/json",
        )
        # View catches exceptions and returns JSON with success=False or HTTP 400
        self.assertIn(resp.status_code, [200, 400])
        if resp.status_code == 200:
            self.assertFalse(resp.json()["success"])


class LoginUserViewTest(TestCase):
    """TDD-10: POST /assignments/login/ endpoint"""

    def setUp(self):
        self.client = Client()
        self.url = "/assignments/login/"
        self.college = make_college()
        self.student = make_student(
            email="login@test.com", password="secret12", college=self.college
        )

    def test_valid_credentials_return_success_true(self):
        resp = self.client.post(
            self.url,
            data=json.dumps({"email": "login@test.com", "password": "secret12"}),
            content_type="application/json",
        )
        data = resp.json()
        self.assertTrue(data["success"])
        self.assertIn("student_id", data)

    def test_wrong_password_returns_success_false(self):
        resp = self.client.post(
            self.url,
            data=json.dumps({"email": "login@test.com", "password": "wrong"}),
            content_type="application/json",
        )
        data = resp.json()
        self.assertFalse(data["success"])

    def test_nonexistent_email_returns_success_false(self):
        resp = self.client.post(
            self.url,
            data=json.dumps({"email": "nobody@test.com", "password": "secret12"}),
            content_type="application/json",
        )
        data = resp.json()
        self.assertFalse(data["success"])

    def test_correct_student_id_returned_on_login(self):
        resp = self.client.post(
            self.url,
            data=json.dumps({"email": "login@test.com", "password": "secret12"}),
            content_type="application/json",
        )
        data = resp.json()
        self.assertEqual(data["student_id"], self.student.id)


class StudentStatusViewTest(TestCase):
    """TDD-11: POST /assignments/student-status/"""

    def setUp(self):
        self.client = Client()
        self.url = "/assignments/student-status/"
        self.college = make_college()
        self.student = make_student(college=self.college)

    def test_returns_all_status_fields(self):
        resp = self.client.post(
            self.url,
            data=json.dumps({"email": self.student.email}),
            content_type="application/json",
        )
        data = resp.json()
        self.assertTrue(data["success"])
        for field in [
            "assignment_status", "group_discussion_status",
            "technical_status", "hr_status", "current_stage",
        ]:
            self.assertIn(field, data)

    def test_unknown_email_returns_success_false(self):
        resp = self.client.post(
            self.url,
            data=json.dumps({"email": "ghost@test.com"}),
            content_type="application/json",
        )
        data = resp.json()
        self.assertFalse(data["success"])


class ExamStatusViewTest(TestCase):
    """TDD-12: POST /assignments/exam-status/"""

    def setUp(self):
        self.client = Client()
        self.url = "/assignments/exam-status/"
        self.college = make_college()
        self.student = make_student(college=self.college)

    def test_exam_active_returns_is_active_true(self):
        ExamSettings.objects.update_or_create(
            college=self.college, defaults={"is_exam_active": True}
        )
        resp = self.client.post(
            self.url,
            data=json.dumps({"email": self.student.email}),
            content_type="application/json",
        )
        data = resp.json()
        self.assertTrue(data["is_active"])

    def test_exam_inactive_returns_is_active_false(self):
        ExamSettings.objects.update_or_create(
            college=self.college, defaults={"is_exam_active": False}
        )
        resp = self.client.post(
            self.url,
            data=json.dumps({"email": self.student.email}),
            content_type="application/json",
        )
        data = resp.json()
        self.assertFalse(data["is_active"])

    def test_rejected_student_cannot_access_exam(self):
        self.student.assignment_status = "rejected"
        self.student.save()
        ExamSettings.objects.update_or_create(
            college=self.college, defaults={"is_exam_active": True}
        )
        resp = self.client.post(
            self.url,
            data=json.dumps({"email": self.student.email}),
            content_type="application/json",
        )
        data = resp.json()
        self.assertFalse(data["is_active"])

    def test_no_email_returns_is_active_false(self):
        resp = self.client.post(
            self.url,
            data=json.dumps({}),
            content_type="application/json",
        )
        data = resp.json()
        self.assertFalse(data["is_active"])


class SubmitAssignmentViewTest(TestCase):
    """TDD-13: POST /assignments/submit/"""

    def setUp(self):
        self.client = Client()
        self.url = "/assignments/submit/"
        self.college = make_college()
        self.student = make_student(college=self.college)

        # Correct answers for all 3 MCQ sections (will yield 100% scores)
        self.full_correct_results = {
            "homepage": {
                "answers": {
                    "q1": "Naive Bayes", "q2": "Reduction in entropy",
                    "q3": "Curse of dimensionality", "q4": "F1-score",
                    "q5": "Both a & c", "q6": "Reward",
                    "q7": "Prevent exploding gradients", "q8": "DBSCAN",
                    "q9": "RNN", "q10": "Dimensionality reduction",
                    "q11": "Bootstrapped data sample", "q12": "Sparse models",
                    "q13": "Random Forest",
                    "q14": "True Positive Rate vs False Positive Rate",
                    "q15": "Variance",
                }
            },
            "coding-theory": {
                "answers": {
                    "ct1": "useEffect", "ct2": "401", "ct3": "Document Store",
                    "ct4": "fs", "ct5": "SELECT DISTINCT", "ct6": "PUSH",
                    "ct7": "REST API and backend routing", "ct8": "27017",
                    "ct9": "z-index", "ct10": "a & c", "ct11": "npm init",
                    "ct12": "Key referencing another table's primary key",
                    "ct13": "Context API", "ct14": "Angular", "ct15": "Stateless",
                }
            },
            "logic-reasoning": {
                "answers": {
                    "lr1": "6 days", "lr2": "30", "lr3": "1000", "lr4": "144",
                    "lr5": "12:16", "lr6": "3", "lr7": "2 hr", "lr8": "144",
                    "lr9": "6 days", "lr10": "3 km/h", "lr11": "24", "lr12": "8",
                    "lr13": "112", "lr14": "5/3", "lr15": "18,000", "lr16": "243",
                    "lr17": "8:15", "lr18": "Chair",
                    "lr19": "Three intersecting circles", "lr20": "All of these",
                }
            },
            "programming-task": {
                "code": "def factorial(n): return 1 if n<=1 else n*factorial(n-1)",
                "language": "python",
                "score": {"percentage": 100},
            },
        }

    def _post(self, results):
        return self.client.post(
            self.url,
            data=json.dumps({
                "student": self.student.email,
                "loginTime": "2025-01-01T00:00:00Z",
                "submissionTime": "2025-01-01T01:00:00Z",
                "results": results,
            }),
            content_type="application/json",
        )

    def test_perfect_answers_yield_200_score(self):
        resp = self._post(self.full_correct_results)
        data = resp.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["total_score"], 200)

    def test_perfect_answers_qualify_student(self):
        resp = self._post(self.full_correct_results)
        data = resp.json()
        self.assertEqual(data["qualification_status"], "QUALIFIED")

    def test_zero_answers_yields_rejected_status(self):
        empty_results = {
            "homepage": {"answers": {}},
            "coding-theory": {"answers": {}},
            "logic-reasoning": {"answers": {}},
            "programming-task": {"code": "", "language": "python", "score": 0},
        }
        resp = self._post(empty_results)
        data = resp.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["qualification_status"], "REJECTED")

    def test_assignment_record_created_in_db(self):
        self._post(self.full_correct_results)
        self.assertTrue(Assignment.objects.filter(student=self.student).exists())

    def test_mcq_answers_saved_to_db(self):
        self._post(self.full_correct_results)
        assignment = Assignment.objects.get(student=self.student)
        count = MCQAnswer.objects.filter(assignment=assignment).count()
        # 15 + 15 + 20 = 50 answers
        self.assertEqual(count, 50)

    def test_programming_task_saved_to_db(self):
        self._post(self.full_correct_results)
        assignment = Assignment.objects.get(student=self.student)
        self.assertTrue(ProgrammingTask.objects.filter(assignment=assignment).exists())

    def test_student_status_updated_to_completed(self):
        self._post(self.full_correct_results)
        self.student.refresh_from_db()
        self.assertEqual(self.student.assignment_status, "completed")

    def test_missing_student_email_returns_failure(self):
        resp = self.client.post(
            self.url,
            data=json.dumps({"results": {}}),
            content_type="application/json",
        )
        data = resp.json()
        self.assertFalse(data["success"])

    def test_programming_score_capped_at_100(self):
        results = dict(self.full_correct_results)
        results["programming-task"] = {
            "code": "# code", "language": "python",
            "score": {"percentage": 150},  # Exceeds 100
        }
        resp = self._post(results)
        assignment = Assignment.objects.get(student=self.student)
        self.assertLessEqual(assignment.programming_score, 100)

    def test_aiml_score_max_is_30(self):
        resp = self._post(self.full_correct_results)
        assignment = Assignment.objects.get(student=self.student)
        self.assertLessEqual(assignment.aiml_score, 30)

    def test_fullstack_score_max_is_30(self):
        resp = self._post(self.full_correct_results)
        assignment = Assignment.objects.get(student=self.student)
        self.assertLessEqual(assignment.fullstack_score, 30)

    def test_logic_score_max_is_40(self):
        resp = self._post(self.full_correct_results)
        assignment = Assignment.objects.get(student=self.student)
        self.assertLessEqual(assignment.logic_score, 40)


class RunCodeViewTest(TestCase):
    """TDD-14: POST /assignments/run-code/"""

    def setUp(self):
        self.client = Client()
        self.url = "/assignments/run-code/"

    def test_valid_leap_year_code_returns_accepted(self):
        code = (
            "year = int(input())\n"
            "if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0):\n"
            "    print('Yes')\n"
            "else:\n"
            "    print('No')\n"
        )
        resp = self.client.post(
            self.url,
            data=json.dumps({"problem": "leap", "code": code}),
            content_type="application/json",
        )
        data = resp.json()
        self.assertEqual(data["status"], "accepted")

    def test_invalid_problem_returns_error(self):
        resp = self.client.post(
            self.url,
            data=json.dumps({"problem": "nonexistent", "code": "print(1)"}),
            content_type="application/json",
        )
        data = resp.json()
        self.assertEqual(data["status"], "error")

    def test_empty_code_returns_error(self):
        resp = self.client.post(
            self.url,
            data=json.dumps({"problem": "leap", "code": ""}),
            content_type="application/json",
        )
        data = resp.json()
        self.assertEqual(data["status"], "error")

    def test_syntax_error_code_returns_compile_error(self):
        resp = self.client.post(
            self.url,
            data=json.dumps({"problem": "leap", "code": "def f(:\n    pass"}),
            content_type="application/json",
        )
        data = resp.json()
        self.assertEqual(data["status"], "compile_error")

    def test_wrong_answer_code_returns_failed(self):
        code = "print('wrong')"
        resp = self.client.post(
            self.url,
            data=json.dumps({"problem": "leap", "code": code}),
            content_type="application/json",
        )
        data = resp.json()
        self.assertIn(data["status"], ["failed", "wrong_answer"])
        self.assertEqual(data["score"], 0)

    def test_score_returned_is_numeric(self):
        code = "print(int(input()))"
        resp = self.client.post(
            self.url,
            data=json.dumps({"problem": "leap", "code": code}),
            content_type="application/json",
        )
        data = resp.json()
        self.assertIsInstance(data["score"], (int, float))

    def test_total_score_for_leap_is_10(self):
        resp = self.client.post(
            self.url,
            data=json.dumps({"problem": "leap", "code": "print('No')"}),
            content_type="application/json",
        )
        data = resp.json()
        self.assertEqual(data["total_score"], 10)

    def test_total_score_for_median_is_50(self):
        resp = self.client.post(
            self.url,
            data=json.dumps({"problem": "median", "code": "print('x')"}),
            content_type="application/json",
        )
        data = resp.json()
        self.assertEqual(data["total_score"], 50)


class SubmitCodeViewTest(TestCase):
    """TDD-15: POST /assignments/submit-code/"""

    def setUp(self):
        self.client = Client()
        self.url = "/assignments/submit-code/"
        self.college = make_college()
        self.student = make_student(college=self.college)

    def test_successful_submission_returns_score(self):
        resp = self.client.post(
            self.url,
            data=json.dumps({
                "student_email": self.student.email,
                "problem": "leap",
                "code": "print('Yes')",
                "result": "passed",
                "score": 10,
            }),
            content_type="application/json",
        )
        data = resp.json()
        self.assertEqual(data["score"], 10)

    def test_missing_email_returns_401(self):
        resp = self.client.post(
            self.url,
            data=json.dumps({"problem": "leap", "code": "x", "score": 5}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 401)

    def test_unknown_student_returns_404(self):
        resp = self.client.post(
            self.url,
            data=json.dumps({
                "student_email": "nobody@test.com",
                "problem": "leap",
                "code": "x",
                "score": 5,
            }),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 404)

    def test_higher_score_updates_evaluation(self):
        # First submission with score 10
        self.client.post(
            self.url,
            data=json.dumps({
                "student_email": self.student.email,
                "problem": "leap",
                "code": "x",
                "result": "ok",
                "score": 10,
            }),
            content_type="application/json",
        )
        # Second submission with higher score 20
        self.client.post(
            self.url,
            data=json.dumps({
                "student_email": self.student.email,
                "problem": "nextprime",
                "code": "x",
                "result": "ok",
                "score": 20,
            }),
            content_type="application/json",
        )
        ev = Evaluation.objects.get(student=self.student)
        self.assertEqual(ev.programming_score, 20)

    def test_code_submission_record_created(self):
        self.client.post(
            self.url,
            data=json.dumps({
                "student_email": self.student.email,
                "problem": "hcf",
                "code": "x",
                "result": "ok",
                "score": 0,
            }),
            content_type="application/json",
        )
        self.assertTrue(
            CodeSubmission.objects.filter(student=self.student, problem="hcf").exists()
        )


# ---------------------------------------------------------------------------
# 3. ADMIN ACTION TESTS
# ---------------------------------------------------------------------------

class AdminRejectAssignmentTest(TestCase):
    """TDD-16: AssignmentAdmin reject action"""

    def setUp(self):
        self.site = AdminSite()
        self.admin = AssignmentAdmin(Assignment, self.site)
        self.request = make_request_with_messages()

    def test_reject_sets_student_assignment_status_rejected(self):
        student = make_student(assignment_status="completed")
        assignment = make_assignment(student)
        qs = Assignment.objects.filter(pk=assignment.pk)
        self.admin.reject_assignment(self.request, qs)
        student.refresh_from_db()
        self.assertEqual(student.assignment_status, "rejected")

    def test_reject_works_for_multiple_students(self):
        s1 = make_student(email="s1@t.com", assignment_status="completed")
        s2 = make_student(email="s2@t.com", assignment_status="completed")
        a1 = make_assignment(s1)
        a2 = make_assignment(s2)
        qs = Assignment.objects.filter(pk__in=[a1.pk, a2.pk])
        self.admin.reject_assignment(self.request, qs)
        s1.refresh_from_db()
        s2.refresh_from_db()
        self.assertEqual(s1.assignment_status, "rejected")
        self.assertEqual(s2.assignment_status, "rejected")


class AdminPushToGDTest(TestCase):
    """TDD-17: AssignmentAdmin push_to_gd action"""

    def setUp(self):
        self.site = AdminSite()
        self.admin = AssignmentAdmin(Assignment, self.site)
        self.request = make_request_with_messages()

    def test_push_creates_group_discussion_record(self):
        student = make_student(assignment_status="completed")
        assignment = make_assignment(student)
        qs = Assignment.objects.filter(pk=assignment.pk)
        self.admin.push_to_gd(self.request, qs)
        self.assertTrue(GroupDiscussion.objects.filter(student=student).exists())

    def test_push_updates_student_stage_to_gd(self):
        student = make_student(assignment_status="completed")
        assignment = make_assignment(student)
        qs = Assignment.objects.filter(pk=assignment.pk)
        self.admin.push_to_gd(self.request, qs)
        student.refresh_from_db()
        self.assertEqual(student.current_stage, "group_discussion")

    def test_push_does_not_duplicate_gd_record(self):
        student = make_student(assignment_status="completed")
        assignment = make_assignment(student)
        qs = Assignment.objects.filter(pk=assignment.pk)
        self.admin.push_to_gd(self.request, qs)
        self.admin.push_to_gd(self.request, qs)  # second push
        self.assertEqual(GroupDiscussion.objects.filter(student=student).count(), 1)


class AdminRejectGroupDiscussionTest(TestCase):
    """TDD-18: GroupDiscussionAdmin reject action"""

    def setUp(self):
        self.site = AdminSite()
        self.admin = GroupDiscussionAdmin(GroupDiscussion, self.site)
        self.request = make_request_with_messages()

    def test_reject_sets_gd_status_rejected(self):
        student = make_student()
        gd = GroupDiscussion.objects.create(student=student, assignment_score=150, gd_score=60)
        qs = GroupDiscussion.objects.filter(pk=gd.pk)
        self.admin.reject_group_discussion(self.request, qs)
        gd.refresh_from_db()
        self.assertEqual(gd.status, "rejected")

    def test_reject_sets_student_gd_status_rejected(self):
        student = make_student()
        gd = GroupDiscussion.objects.create(student=student, assignment_score=150, gd_score=60)
        qs = GroupDiscussion.objects.filter(pk=gd.pk)
        self.admin.reject_group_discussion(self.request, qs)
        student.refresh_from_db()
        self.assertEqual(student.group_discussion_status, "rejected")


class AdminPushToTechnicalTest(TestCase):
    """TDD-19: GroupDiscussionAdmin push_to_technical action"""

    def setUp(self):
        self.site = AdminSite()
        self.admin = GroupDiscussionAdmin(GroupDiscussion, self.site)
        self.request = make_request_with_messages()

    def test_push_creates_technical_round_record(self):
        student = make_student()
        gd = GroupDiscussion.objects.create(
            student=student, assignment_score=150, gd_score=60, status="pending"
        )
        qs = GroupDiscussion.objects.filter(pk=gd.pk)
        self.admin.push_to_technical(self.request, qs)
        self.assertTrue(TechnicalRound.objects.filter(student=student).exists())

    def test_push_updates_student_stage_to_technical(self):
        student = make_student()
        gd = GroupDiscussion.objects.create(
            student=student, assignment_score=150, gd_score=60, status="pending"
        )
        qs = GroupDiscussion.objects.filter(pk=gd.pk)
        self.admin.push_to_technical(self.request, qs)
        student.refresh_from_db()
        self.assertEqual(student.current_stage, "technical")


class AdminRejectTechnicalRoundTest(TestCase):
    """TDD-20: TechnicalRoundAdmin reject action"""

    def setUp(self):
        self.site = AdminSite()
        self.admin = TechnicalRoundAdmin(TechnicalRound, self.site)
        self.request = make_request_with_messages()

    def test_reject_sets_technical_status_rejected(self):
        student = make_student()
        tr = TechnicalRound.objects.create(
            student=student, assignment_score=150, gd_score=60, technical_score=70
        )
        qs = TechnicalRound.objects.filter(pk=tr.pk)
        self.admin.reject_technical(self.request, qs)
        tr.refresh_from_db()
        self.assertEqual(tr.status, "rejected")

    def test_reject_sets_student_technical_status_rejected(self):
        student = make_student()
        tr = TechnicalRound.objects.create(
            student=student, assignment_score=150, gd_score=60, technical_score=70
        )
        qs = TechnicalRound.objects.filter(pk=tr.pk)
        self.admin.reject_technical(self.request, qs)
        student.refresh_from_db()
        self.assertEqual(student.technical_status, "rejected")


class AdminPushToHRTest(TestCase):
    """TDD-21: TechnicalRoundAdmin push_to_hr action"""

    def setUp(self):
        self.site = AdminSite()
        self.admin = TechnicalRoundAdmin(TechnicalRound, self.site)
        self.request = make_request_with_messages()

    def test_push_creates_hr_round_record(self):
        student = make_student()
        tr = TechnicalRound.objects.create(
            student=student, assignment_score=150, gd_score=60,
            technical_score=70, status="pending"
        )
        qs = TechnicalRound.objects.filter(pk=tr.pk)
        self.admin.push_to_hr(self.request, qs)
        self.assertTrue(HRRound.objects.filter(student=student).exists())

    def test_push_updates_student_stage_to_hr(self):
        student = make_student()
        tr = TechnicalRound.objects.create(
            student=student, assignment_score=150, gd_score=60,
            technical_score=70, status="pending"
        )
        qs = TechnicalRound.objects.filter(pk=tr.pk)
        self.admin.push_to_hr(self.request, qs)
        student.refresh_from_db()
        self.assertEqual(student.current_stage, "hr_round")


class AdminRejectHRRoundTest(TestCase):
    """TDD-22: HRRoundAdmin reject action"""

    def setUp(self):
        self.site = AdminSite()
        self.admin = HRRoundAdmin(HRRound, self.site)
        self.request = make_request_with_messages()

    def test_reject_sets_hr_status_rejected(self):
        student = make_student()
        hr = HRRound.objects.create(
            student=student, assignment_score=150, gd_score=60,
            technical_score=70, hr_score=80
        )
        qs = HRRound.objects.filter(pk=hr.pk)
        self.admin.reject_hr(self.request, qs)
        hr.refresh_from_db()
        self.assertEqual(hr.status, "rejected")

    def test_reject_sets_student_hr_status_rejected(self):
        student = make_student()
        hr = HRRound.objects.create(
            student=student, assignment_score=150, gd_score=60,
            technical_score=70, hr_score=80
        )
        qs = HRRound.objects.filter(pk=hr.pk)
        self.admin.reject_hr(self.request, qs)
        student.refresh_from_db()
        self.assertEqual(student.hr_status, "rejected")


class AdminMarkSelectedTest(TestCase):
    """TDD-23: HRRoundAdmin mark_selected action"""

    def setUp(self):
        self.site = AdminSite()
        self.admin = HRRoundAdmin(HRRound, self.site)
        self.request = make_request_with_messages()

    def test_mark_selected_sets_hr_status_selected(self):
        student = make_student()
        hr = HRRound.objects.create(
            student=student, assignment_score=150, gd_score=60,
            technical_score=70, hr_score=80, status="pending"
        )
        qs = HRRound.objects.filter(pk=hr.pk)
        self.admin.mark_selected(self.request, qs)
        hr.refresh_from_db()
        self.assertEqual(hr.status, "selected")

    def test_mark_selected_sets_student_hr_status_qualified(self):
        student = make_student()
        hr = HRRound.objects.create(
            student=student, assignment_score=150, gd_score=60,
            technical_score=70, hr_score=80, status="pending"
        )
        qs = HRRound.objects.filter(pk=hr.pk)
        self.admin.mark_selected(self.request, qs)
        student.refresh_from_db()
        self.assertEqual(student.hr_status, "qualified")


class StudentAdminActionsTest(TestCase):
    """TDD-24: StudentAdmin round approve / reject actions"""

    def setUp(self):
        self.site = AdminSite()
        self.admin = StudentAdmin(Student, self.site)
        self.request = make_request_with_messages()
        self.college = make_college()

    def test_approve_assignment_moves_student_to_gd(self):
        student = make_student(college=self.college, assignment_status="completed")
        qs = Student.objects.filter(pk=student.pk)
        self.admin.approve_assignment(self.request, qs)
        student.refresh_from_db()
        self.assertEqual(student.assignment_status, "qualified")
        self.assertEqual(student.current_stage, "group_discussion")

    def test_reject_assignment_keeps_student_rejected(self):
        student = make_student(college=self.college, assignment_status="completed")
        qs = Student.objects.filter(pk=student.pk)
        self.admin.reject_assignment(self.request, qs)
        student.refresh_from_db()
        self.assertEqual(student.assignment_status, "rejected")

    def test_approve_gd_moves_student_to_technical(self):
        student = make_student(college=self.college)
        student.group_discussion_status = "completed"
        student.save()
        qs = Student.objects.filter(pk=student.pk)
        self.admin.approve_group_discussion(self.request, qs)
        student.refresh_from_db()
        self.assertEqual(student.group_discussion_status, "qualified")
        self.assertEqual(student.current_stage, "technical")

    def test_approve_technical_moves_student_to_hr(self):
        student = make_student(college=self.college)
        student.technical_status = "completed"
        student.save()
        qs = Student.objects.filter(pk=student.pk)
        self.admin.approve_technical(self.request, qs)
        student.refresh_from_db()
        self.assertEqual(student.technical_status, "qualified")
        self.assertEqual(student.current_stage, "hr_round")

    def test_approve_hr_qualifies_student(self):
        student = make_student(college=self.college)
        student.hr_status = "completed"
        student.save()
        qs = Student.objects.filter(pk=student.pk)
        self.admin.approve_hr(self.request, qs)
        student.refresh_from_db()
        self.assertEqual(student.hr_status, "qualified")
