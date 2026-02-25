"""
BDD (Behaviour-Driven Development) Tests for Exam Portal
=========================================================
Tests are written in a Given / When / Then style and describe the system
from the perspective of the student, the admin, and the exam lifecycle.

Each test class represents one *feature* (user-story level). Individual
test methods are the *scenarios* within that feature.

Run:
    docker exec exam_portal python manage.py test assignments.tests.test_bdd -v 2
"""

import json
from django.test import TestCase, Client
from django.contrib.admin.sites import AdminSite
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import RequestFactory

from assignments.models import (
    College, ExamSettings, Student, Assignment,
    MCQAnswer, GroupDiscussion, TechnicalRound,
    HRRound, Evaluation, CodeSubmission,
)
from assignments.admin import (
    AssignmentAdmin, GroupDiscussionAdmin,
    TechnicalRoundAdmin, HRRoundAdmin, StudentAdmin,
)


# ---------------------------------------------------------------------------
# Helpers (same lightweight fixtures as in TDD tests)
# ---------------------------------------------------------------------------

def _college(name="College BDD", code="BDD01", active=True):
    c, _ = College.objects.get_or_create(
        code=code,
        defaults={"name": name, "is_active": active},
    )
    return c


def _exam_settings(college, active=False):
    es, _ = ExamSettings.objects.get_or_create(
        college=college,
        defaults={"is_exam_active": active},
    )
    return es


def _student(email, name="Student", password="pass1234", college=None,
             assignment_status="pending"):
    if college is None:
        college = _college()
    return Student.objects.create(
        name=name, email=email, mobile="9999999999",
        roll_number="R001", stream="CSE", skills="Python",
        college_name=college.name,
        ssc_grade="8.5", intermediate_grade="8.0",
        current_semester_cgpa="7.5",
        password=password, college=college,
        assignment_status=assignment_status,
    )


def _assignment(student, aiml=20, fullstack=20, logic=30, prog=80):
    a = Assignment.objects.create(
        student=student,
        aiml_score=aiml, fullstack_score=fullstack,
        logic_score=logic, programming_score=prog,
    )
    a.calculate_final_score()
    a.save()
    return a


def _request_with_messages():
    factory = RequestFactory()
    req = factory.get("/")
    req.session = {}
    req._messages = FallbackStorage(req)
    return req


# ---------------------------------------------------------------------------
# Feature 1 – Student Registration
# ---------------------------------------------------------------------------

class Feature_StudentRegistration(TestCase):
    """
    Feature: Student Registration
      As a prospective candidate
      I want to register with my academic details
      So that I can access the exam platform
    """

    def setUp(self):
        self.client = Client()
        self.url = "/assignments/register/"

    # ------------------------------------------------------------------
    # Scenario 1: Successful new registration
    # ------------------------------------------------------------------
    def test_scenario_successful_new_registration(self):
        # GIVEN no student with the email exists
        self.assertFalse(Student.objects.filter(email="bdd_new@test.com").exists())

        # WHEN the student submits a complete registration form
        resp = self.client.post(
            self.url,
            data=json.dumps({
                "name": "BDD Student",
                "email": "bdd_new@test.com",
                "mobile": "9876543210",
                "roll_number": "BDD001",
                "stream": "CSE",
                "skills": "Django, React",
                "college_name": "BDD University",
                "ssc_grade": "9.2",
                "intermediate_grade": "8.8",
                "current_semester_cgpa": "8.5",
                "password": "secure99",
            }),
            content_type="application/json",
        )

        # THEN registration succeeds
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["success"])

        # AND the student record is persisted
        self.assertTrue(Student.objects.filter(email="bdd_new@test.com").exists())

    # ------------------------------------------------------------------
    # Scenario 2: Duplicate email rejected
    # ------------------------------------------------------------------
    def test_scenario_duplicate_email_is_rejected(self):
        # GIVEN a student is already registered with an email
        _student("dup_bdd@test.com")

        # WHEN another registration attempt uses the same email
        resp = self.client.post(
            self.url,
            data=json.dumps({
                "name": "Another Person",
                "email": "dup_bdd@test.com",
                "mobile": "1111111111",
                "roll_number": "X999",
                "stream": "ECE",
                "skills": "Java",
                "college_name": "Some College",
                "ssc_grade": "7.0",
                "intermediate_grade": "6.5",
                "current_semester_cgpa": "6.0",
                "password": "test1234",
            }),
            content_type="application/json",
        )

        # THEN the system rejects the request
        data = resp.json()
        self.assertFalse(data["success"])
        self.assertIn("already registered", data["message"])

        # AND only one student record exists for that email
        self.assertEqual(Student.objects.filter(email="dup_bdd@test.com").count(), 1)

    # ------------------------------------------------------------------
    # Scenario 3: College and ExamSettings are auto-created
    # ------------------------------------------------------------------
    def test_scenario_new_college_and_exam_settings_created_on_registration(self):
        # GIVEN the college "Brand New University" does not exist
        self.assertFalse(College.objects.filter(name="Brand New University").exists())

        # WHEN a student from that college registers
        self.client.post(
            self.url,
            data=json.dumps({
                "name": "First Student",
                "email": "first@brandnew.com",
                "mobile": "9000000000",
                "roll_number": "F001",
                "stream": "IT",
                "skills": "SQL",
                "college_name": "Brand New University",
                "ssc_grade": "8.0",
                "intermediate_grade": "7.5",
                "current_semester_cgpa": "7.0",
                "password": "test1234",
            }),
            content_type="application/json",
        )

        # THEN the college is created
        college = College.objects.filter(name="Brand New University").first()
        self.assertIsNotNone(college)

        # AND exam settings (inactive by default) are created for that college
        self.assertTrue(ExamSettings.objects.filter(college=college).exists())
        es = ExamSettings.objects.get(college=college)
        self.assertFalse(es.is_exam_active)


# ---------------------------------------------------------------------------
# Feature 2 – Student Login
# ---------------------------------------------------------------------------

class Feature_StudentLogin(TestCase):
    """
    Feature: Student Login
      As a registered student
      I want to log in with my email and password
      So that I can access my dashboard
    """

    def setUp(self):
        self.client = Client()
        self.url = "/assignments/login/"
        self.college = _college(code="LGN01")
        self.student = _student("bdd_login@test.com", password="mypass88",
                                college=self.college)

    def test_scenario_valid_credentials_grant_access(self):
        # GIVEN a registered student with correct credentials
        # WHEN the student submits the login form
        resp = self.client.post(
            self.url,
            data=json.dumps({"email": "bdd_login@test.com", "password": "mypass88"}),
            content_type="application/json",
        )

        # THEN login is successful and student_id is returned
        data = resp.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["student_id"], self.student.id)

    def test_scenario_wrong_password_denies_access(self):
        # GIVEN a registered student
        # WHEN the student submits an incorrect password
        resp = self.client.post(
            self.url,
            data=json.dumps({"email": "bdd_login@test.com", "password": "wrongpass"}),
            content_type="application/json",
        )

        # THEN access is denied
        data = resp.json()
        self.assertFalse(data["success"])

    def test_scenario_unknown_email_denies_access(self):
        # GIVEN an email that is not registered
        # WHEN login is attempted with that email
        resp = self.client.post(
            self.url,
            data=json.dumps({"email": "ghost@noemail.com", "password": "mypass88"}),
            content_type="application/json",
        )

        # THEN access is denied
        data = resp.json()
        self.assertFalse(data["success"])


# ---------------------------------------------------------------------------
# Feature 3 – Exam Access Control
# ---------------------------------------------------------------------------

class Feature_ExamAccessControl(TestCase):
    """
    Feature: Exam Access Control
      As an admin
      I want to control when and for whom the exam is available
      So that students only sit the exam at the scheduled time
    """

    def setUp(self):
        self.client = Client()
        self.url = "/assignments/exam-status/"
        self.college = _college(code="EAC01")
        self.student = _student("bdd_eac@test.com", college=self.college)

    def test_scenario_exam_not_active_blocks_student(self):
        # GIVEN the exam is not activated for the student's college
        ExamSettings.objects.update_or_create(
            college=self.college, defaults={"is_exam_active": False}
        )

        # WHEN the student checks exam status
        resp = self.client.post(
            self.url,
            data=json.dumps({"email": self.student.email}),
            content_type="application/json",
        )

        # THEN the student is told the exam is inactive
        data = resp.json()
        self.assertFalse(data["is_active"])

    def test_scenario_exam_active_allows_student(self):
        # GIVEN the admin has activated the exam for the college
        ExamSettings.objects.update_or_create(
            college=self.college, defaults={"is_exam_active": True}
        )

        # WHEN the student checks exam status
        resp = self.client.post(
            self.url,
            data=json.dumps({"email": self.student.email}),
            content_type="application/json",
        )

        # THEN the student is allowed access
        data = resp.json()
        self.assertTrue(data["is_active"])

    def test_scenario_rejected_student_cannot_access_even_if_exam_active(self):
        # GIVEN the exam is active but the student was previously rejected
        ExamSettings.objects.update_or_create(
            college=self.college, defaults={"is_exam_active": True}
        )
        self.student.assignment_status = "rejected"
        self.student.save()

        # WHEN the student checks exam status
        resp = self.client.post(
            self.url,
            data=json.dumps({"email": self.student.email}),
            content_type="application/json",
        )

        # THEN access is permanently denied
        data = resp.json()
        self.assertFalse(data["is_active"])
        self.assertIn("denied", data["message"].lower())


# ---------------------------------------------------------------------------
# Feature 4 – Assignment Submission and Scoring
# ---------------------------------------------------------------------------

class Feature_AssignmentSubmission(TestCase):
    """
    Feature: Assignment Submission
      As a student
      I want to submit my MCQ answers and code
      So that I can be evaluated and move to the next round
    """

    def setUp(self):
        self.client = Client()
        self.url = "/assignments/submit/"
        self.college = _college(code="ASS01")
        self.student = _student("bdd_submit@test.com", college=self.college)

        self.all_correct_results = {
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

    def _post_submission(self, results):
        return self.client.post(
            self.url,
            data=json.dumps({
                "student": self.student.email,
                "loginTime": "2025-01-01T09:00:00Z",
                "submissionTime": "2025-01-01T10:00:00Z",
                "results": results,
            }),
            content_type="application/json",
        )

    def test_scenario_student_who_answers_all_correctly_gets_200(self):
        # GIVEN a student who answered all 50 MCQ questions correctly
        # AND submitted working code

        # WHEN the assignment is submitted
        resp = self._post_submission(self.all_correct_results)

        # THEN the total score is 200 out of 200
        data = resp.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["total_score"], 200)
        self.assertEqual(data["qualification_status"], "QUALIFIED")

    def test_scenario_student_with_zero_correct_answers_fails(self):
        # GIVEN a student who answered nothing
        empty = {
            "homepage": {"answers": {}},
            "coding-theory": {"answers": {}},
            "logic-reasoning": {"answers": {}},
            "programming-task": {"code": "", "language": "python", "score": 0},
        }

        # WHEN the assignment is submitted
        resp = self._post_submission(empty)

        # THEN the student is marked as REJECTED
        data = resp.json()
        self.assertEqual(data["qualification_status"], "REJECTED")
        self.assertEqual(data["total_score"], 0)

    def test_scenario_submission_marks_student_status_as_completed(self):
        # GIVEN a student who just finished the exam
        # WHEN submission is sent
        self._post_submission(self.all_correct_results)

        # THEN the student's assignment_status is 'completed'
        self.student.refresh_from_db()
        self.assertEqual(self.student.assignment_status, "completed")

    def test_scenario_mcq_answers_are_persisted(self):
        # GIVEN all 50 correct answers submitted
        # WHEN the assignment is submitted
        self._post_submission(self.all_correct_results)

        # THEN 50 MCQAnswer records exist for this student
        assignment = Assignment.objects.get(student=self.student)
        self.assertEqual(MCQAnswer.objects.filter(assignment=assignment).count(), 50)

    def test_scenario_scores_per_section_are_bounded_by_max(self):
        # GIVEN a full submission
        # WHEN it is evaluated
        self._post_submission(self.all_correct_results)
        a = Assignment.objects.get(student=self.student)

        # THEN each section score does not exceed its maximum
        self.assertLessEqual(a.aiml_score, 30)        # 15 × 2
        self.assertLessEqual(a.fullstack_score, 30)   # 15 × 2
        self.assertLessEqual(a.logic_score, 40)       # 20 × 2
        self.assertLessEqual(a.programming_score, 100)


# ---------------------------------------------------------------------------
# Feature 5 – Admin Pipeline: Assignment → GD → Technical → HR
# ---------------------------------------------------------------------------

class Feature_AdminRecruitmentPipeline(TestCase):
    """
    Feature: Admin Recruitment Pipeline
      As an admin
      I want to push qualified students through each interview stage
      So that the recruitment process progresses systematically
    """

    def setUp(self):
        self.site = AdminSite()
        self.request = _request_with_messages()
        self.college = _college(code="ARP01")

    # ------------------------------------------------------------------
    # Scenario: Pushing a student from Assignment to GD
    # ------------------------------------------------------------------
    def test_scenario_admin_promotes_qualified_student_to_gd(self):
        # GIVEN a student who passed the assignment
        student = _student("bdd_promote@test.com", college=self.college,
                           assignment_status="completed")
        assignment = _assignment(student, aiml=30, fullstack=30, logic=40, prog=100)

        admin = AssignmentAdmin(Assignment, self.site)

        # WHEN the admin selects the student and uses 'Push to GD'
        qs = Assignment.objects.filter(pk=assignment.pk)
        admin.push_to_gd(self.request, qs)

        # THEN a GroupDiscussion record is created
        self.assertTrue(GroupDiscussion.objects.filter(student=student).exists())

        # AND the student's stage advances to group_discussion
        student.refresh_from_db()
        self.assertEqual(student.current_stage, "group_discussion")
        self.assertEqual(student.assignment_status, "qualified")

    # ------------------------------------------------------------------
    # Scenario: Rejecting a student at Assignment stage
    # ------------------------------------------------------------------
    def test_scenario_admin_rejects_student_at_assignment(self):
        # GIVEN a student who just completed the assignment
        student = _student("bdd_reject_asn@test.com", college=self.college,
                           assignment_status="completed")
        assignment = _assignment(student, aiml=5, fullstack=5, logic=5, prog=5)

        admin = AssignmentAdmin(Assignment, self.site)

        # WHEN the admin rejects the student
        qs = Assignment.objects.filter(pk=assignment.pk)
        admin.reject_assignment(self.request, qs)

        # THEN the student's assignment status is 'rejected'
        student.refresh_from_db()
        self.assertEqual(student.assignment_status, "rejected")

        # AND the student cannot access the exam again (checked via API below)
        client = Client()
        _exam_settings(self.college, active=True)
        resp = client.post(
            "/assignments/exam-status/",
            data=json.dumps({"email": student.email}),
            content_type="application/json",
        )
        self.assertFalse(resp.json()["is_active"])

    # ------------------------------------------------------------------
    # Scenario: GD → Technical promotion
    # ------------------------------------------------------------------
    def test_scenario_admin_promotes_student_from_gd_to_technical(self):
        # GIVEN a student in Group Discussion stage
        student = _student("bdd_gd_tech@test.com", college=self.college)
        assignment = _assignment(student, aiml=30, fullstack=30, logic=40, prog=100)
        gd = GroupDiscussion.objects.create(
            student=student, assignment_score=assignment.total_score,
            gd_score=80, status="pending"
        )

        admin = GroupDiscussionAdmin(GroupDiscussion, self.site)

        # WHEN the admin uses 'Push to Technical'
        qs = GroupDiscussion.objects.filter(pk=gd.pk)
        admin.push_to_technical(self.request, qs)

        # THEN a TechnicalRound record is created
        self.assertTrue(TechnicalRound.objects.filter(student=student).exists())

        # AND the student advances to the technical stage
        student.refresh_from_db()
        self.assertEqual(student.current_stage, "technical")

    # ------------------------------------------------------------------
    # Scenario: Technical → HR promotion
    # ------------------------------------------------------------------
    def test_scenario_admin_promotes_student_from_technical_to_hr(self):
        # GIVEN a student who passed the technical round
        student = _student("bdd_tech_hr@test.com", college=self.college)
        tr = TechnicalRound.objects.create(
            student=student, assignment_score=160, gd_score=80,
            technical_score=85, status="pending"
        )

        admin = TechnicalRoundAdmin(TechnicalRound, self.site)

        # WHEN the admin uses 'Push to HR'
        qs = TechnicalRound.objects.filter(pk=tr.pk)
        admin.push_to_hr(self.request, qs)

        # THEN an HRRound record is created
        self.assertTrue(HRRound.objects.filter(student=student).exists())

        # AND the student advances to hr_round stage
        student.refresh_from_db()
        self.assertEqual(student.current_stage, "hr_round")

    # ------------------------------------------------------------------
    # Scenario: HR round final selection
    # ------------------------------------------------------------------
    def test_scenario_admin_marks_student_as_finally_selected(self):
        # GIVEN a student who completed the HR round
        student = _student("bdd_hr_final@test.com", college=self.college)
        hr = HRRound.objects.create(
            student=student, assignment_score=160, gd_score=80,
            technical_score=85, hr_score=90, status="pending"
        )

        admin = HRRoundAdmin(HRRound, self.site)

        # WHEN the admin marks the student as 'Selected'
        qs = HRRound.objects.filter(pk=hr.pk)
        admin.mark_selected(self.request, qs)

        # THEN the HR round status is 'selected'
        hr.refresh_from_db()
        self.assertEqual(hr.status, "selected")

        # AND the student's hr_status is 'qualified'
        student.refresh_from_db()
        self.assertEqual(student.hr_status, "qualified")

    # ------------------------------------------------------------------
    # Scenario: Reject at each late stage
    # ------------------------------------------------------------------
    def test_scenario_admin_rejects_student_at_gd_stage(self):
        student = _student("bdd_reject_gd@test.com", college=self.college)
        gd = GroupDiscussion.objects.create(student=student, assignment_score=160, gd_score=30)

        admin = GroupDiscussionAdmin(GroupDiscussion, self.site)
        qs = GroupDiscussion.objects.filter(pk=gd.pk)
        admin.reject_group_discussion(self.request, qs)

        gd.refresh_from_db()
        student.refresh_from_db()
        self.assertEqual(gd.status, "rejected")
        self.assertEqual(student.group_discussion_status, "rejected")

    def test_scenario_admin_rejects_student_at_technical_stage(self):
        student = _student("bdd_reject_tech@test.com", college=self.college)
        tr = TechnicalRound.objects.create(
            student=student, assignment_score=160, gd_score=80, technical_score=20
        )

        admin = TechnicalRoundAdmin(TechnicalRound, self.site)
        qs = TechnicalRound.objects.filter(pk=tr.pk)
        admin.reject_technical(self.request, qs)

        tr.refresh_from_db()
        student.refresh_from_db()
        self.assertEqual(tr.status, "rejected")
        self.assertEqual(student.technical_status, "rejected")

    def test_scenario_admin_rejects_student_at_hr_stage(self):
        student = _student("bdd_reject_hr@test.com", college=self.college)
        hr = HRRound.objects.create(
            student=student, assignment_score=160, gd_score=80,
            technical_score=85, hr_score=25
        )

        admin = HRRoundAdmin(HRRound, self.site)
        qs = HRRound.objects.filter(pk=hr.pk)
        admin.reject_hr(self.request, qs)

        hr.refresh_from_db()
        student.refresh_from_db()
        self.assertEqual(hr.status, "rejected")
        self.assertEqual(student.hr_status, "rejected")


# ---------------------------------------------------------------------------
# Feature 6 – Score Calculation Integrity
# ---------------------------------------------------------------------------

class Feature_ScoreCalculationIntegrity(TestCase):
    """
    Feature: Score Calculation Integrity
      As a system
      I want to calculate scores deterministically
      So that all students are evaluated consistently and fairly
    """

    def setUp(self):
        self.student = _student("bdd_score@test.com")

    def test_scenario_assignment_total_is_sum_of_four_sections(self):
        # GIVEN individual section scores
        # WHEN calculate_final_score is called
        a = Assignment(
            student=self.student,
            aiml_score=24, fullstack_score=20,
            logic_score=36, programming_score=75,
        )
        total = a.calculate_final_score()

        # THEN total = 24 + 20 + 36 + 75 = 155
        self.assertEqual(total, 155)
        self.assertEqual(a.total_score, 155)

    def test_scenario_student_with_score_160_exactly_is_qualified(self):
        # GIVEN exactly boundary score
        a = Assignment(
            student=self.student,
            aiml_score=30, fullstack_score=30,
            logic_score=40, programming_score=60,
        )
        a.calculate_final_score()

        # THEN student is qualified (≥ 160)
        self.assertTrue(a.is_passed)

    def test_scenario_student_with_score_159_is_not_qualified(self):
        a = Assignment(
            student=self.student,
            aiml_score=30, fullstack_score=29,
            logic_score=40, programming_score=60,
        )
        a.calculate_final_score()
        self.assertFalse(a.is_passed)

    def test_scenario_gd_total_is_assignment_plus_gd_score(self):
        gd = GroupDiscussion(student=self.student, assignment_score=170, gd_score=65)
        self.assertEqual(gd.calculate_total_score(), 235)

    def test_scenario_technical_total_includes_all_three_stages(self):
        tr = TechnicalRound(
            student=self.student,
            assignment_score=170, gd_score=65, technical_score=80
        )
        self.assertEqual(tr.calculate_total_score(), 315)

    def test_scenario_hr_total_includes_all_four_stages(self):
        hr = HRRound(
            student=self.student,
            assignment_score=170, gd_score=65,
            technical_score=80, hr_score=90
        )
        self.assertEqual(hr.calculate_total_score(), 405)

    def test_scenario_evaluation_pass_threshold_is_50_percent(self):
        # GIVEN a student with average of exactly 50
        ev = Evaluation.objects.create(
            student=self.student,
            gd_score=50, technical_score=50, hr_score=50
        )
        self.assertEqual(ev.status, "Pass")

    def test_scenario_evaluation_fail_when_average_below_50(self):
        ev = Evaluation.objects.create(
            student=self.student,
            gd_score=40, technical_score=45, hr_score=48
        )
        self.assertEqual(ev.status, "Fail")

    def test_scenario_evaluation_excludes_zero_scores_from_average(self):
        # Only two non-zero scores: 60, 80 → average = 70 → Pass
        ev = Evaluation.objects.create(
            student=self.student,
            gd_score=60, technical_score=0, hr_score=80
        )
        self.assertAlmostEqual(ev.final_weighted_score, 70.0)
        self.assertEqual(ev.status, "Pass")


# ---------------------------------------------------------------------------
# Feature 7 – Coding Platform
# ---------------------------------------------------------------------------

class Feature_CodingPlatform(TestCase):
    """
    Feature: Coding Platform
      As a student
      I want to write and test Python code for given problems
      So that I can earn marks for the programming section
    """

    def setUp(self):
        self.client = Client()
        self.run_url = "/assignments/run-code/"
        self.submit_url = "/assignments/submit-code/"
        self.college = _college(code="CPL01")
        self.student = _student("bdd_code@test.com", college=self.college)

    def test_scenario_correct_leap_year_code_passes_all_tests(self):
        # GIVEN correct Python code for the leap year problem
        code = (
            "year = int(input())\n"
            "if (year % 4 == 0 and year % 100 != 0) or year % 400 == 0:\n"
            "    print('Yes')\n"
            "else:\n"
            "    print('No')\n"
        )

        # WHEN the student runs it
        resp = self.client.post(
            self.run_url,
            data=json.dumps({"problem": "leap", "code": code}),
            content_type="application/json",
        )

        # THEN all tests pass and score equals the full marks (10)
        data = resp.json()
        self.assertEqual(data["status"], "accepted")
        self.assertEqual(data["score"], 10)

    def test_scenario_correct_hcf_code_passes_all_tests(self):
        code = (
            "import math\n"
            "a = int(input())\n"
            "b = int(input())\n"
            "print(math.gcd(a, b))\n"
        )
        resp = self.client.post(
            self.run_url,
            data=json.dumps({"problem": "hcf", "code": code}),
            content_type="application/json",
        )
        data = resp.json()
        self.assertEqual(data["status"], "accepted")
        self.assertEqual(data["score"], 20)

    def test_scenario_student_can_submit_code_and_score_is_stored(self):
        # GIVEN a student who ran code and got a score of 10
        # WHEN the student submits the code
        resp = self.client.post(
            self.submit_url,
            data=json.dumps({
                "student_email": self.student.email,
                "problem": "leap",
                "code": "year = int(input()); print('Yes')",
                "result": "partial",
                "score": 10,
            }),
            content_type="application/json",
        )

        # THEN the submission is saved
        data = resp.json()
        self.assertEqual(data["score"], 10)
        self.assertTrue(
            CodeSubmission.objects.filter(student=self.student, problem="leap").exists()
        )

    def test_scenario_higher_score_replaces_lower_in_evaluation(self):
        # GIVEN a student with an existing evaluation score of 10
        self.client.post(
            self.submit_url,
            data=json.dumps({
                "student_email": self.student.email,
                "problem": "leap",
                "code": "x", "result": "ok", "score": 10,
            }),
            content_type="application/json",
        )

        # WHEN the student submits a better attempt
        self.client.post(
            self.submit_url,
            data=json.dumps({
                "student_email": self.student.email,
                "problem": "nextprime",
                "code": "x", "result": "ok", "score": 20,
            }),
            content_type="application/json",
        )

        # THEN the evaluation reflects the higher score
        ev = Evaluation.objects.get(student=self.student)
        self.assertEqual(ev.programming_score, 20)

    def test_scenario_unauthenticated_submit_returns_401(self):
        # GIVEN a request with no student email
        resp = self.client.post(
            self.submit_url,
            data=json.dumps({"problem": "leap", "code": "x", "score": 5}),
            content_type="application/json",
        )

        # THEN the server returns 401 Unauthorized
        self.assertEqual(resp.status_code, 401)


# ---------------------------------------------------------------------------
# Feature 8 – Student Status Tracking
# ---------------------------------------------------------------------------

class Feature_StudentStatusTracking(TestCase):
    """
    Feature: Student Status Tracking
      As a student
      I want to query my current stage and round statuses
      So that I can understand what comes next in the process
    """

    def setUp(self):
        self.client = Client()
        self.url = "/assignments/student-status/"
        self.college = _college(code="SST01")
        self.student = _student("bdd_status@test.com", college=self.college)

    def test_scenario_fresh_student_is_in_assignment_stage(self):
        # GIVEN a newly registered student
        # WHEN querying their status
        resp = self.client.post(
            self.url,
            data=json.dumps({"email": self.student.email}),
            content_type="application/json",
        )

        # THEN stage is 'assignment' and all statuses are 'pending'
        data = resp.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["current_stage"], "assignment")
        self.assertEqual(data["assignment_status"], "pending")
        self.assertEqual(data["group_discussion_status"], "pending")
        self.assertEqual(data["technical_status"], "pending")
        self.assertEqual(data["hr_status"], "pending")

    def test_scenario_status_reflects_database_changes(self):
        # GIVEN the admin has updated the student's stage
        self.student.assignment_status = "qualified"
        self.student.current_stage = "group_discussion"
        self.student.group_discussion_status = "in_progress"
        self.student.save()

        # WHEN querying their status
        resp = self.client.post(
            self.url,
            data=json.dumps({"email": self.student.email}),
            content_type="application/json",
        )

        # THEN the response reflects the updated stage
        data = resp.json()
        self.assertEqual(data["current_stage"], "group_discussion")
        self.assertEqual(data["assignment_status"], "qualified")
        self.assertEqual(data["group_discussion_status"], "in_progress")

    def test_scenario_unknown_student_returns_failure(self):
        # GIVEN an email that does not correspond to any student
        resp = self.client.post(
            self.url,
            data=json.dumps({"email": "nobody@nowhere.com"}),
            content_type="application/json",
        )

        # THEN the API returns a failure response
        data = resp.json()
        self.assertFalse(data["success"])
