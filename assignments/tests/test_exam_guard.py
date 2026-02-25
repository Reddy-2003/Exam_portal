"""
TDD + BDD Tests — exam-guard.js integration
=============================================
These tests verify:
  1. All 4 exam pages include exam-guard.js (back-nav + tab-switch guard)
  2. All 4 exam pages no longer contain the old conflicting inline popstate handler
  3. The exam pages are accessible when the app is running
  4. BDD scenarios for the exam integrity features

Run:
    docker exec exam_portal python manage.py test assignments.tests.test_exam_guard -v 2
"""

from django.test import TestCase, Client


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_page(client, url):
    """Return decoded HTML for a page, following redirects."""
    resp = client.get(url)
    return resp.status_code, resp.content.decode('utf-8', errors='replace')


def _get_static(client, url):
    """
    Return decoded content for a static file.
    WhiteNoise uses StreamingHttpResponse so we must read streaming_content.
    """
    resp = client.get(url)
    if resp.status_code != 200:
        return resp.status_code, ''
    try:
        # WhiteNoise streaming response
        raw = b''.join(resp.streaming_content)
    except AttributeError:
        # Regular response (e.g. in DEBUG mode)
        raw = resp.content
    return resp.status_code, raw.decode('utf-8', errors='replace')


# ---------------------------------------------------------------------------
# TDD — Back Navigation Guard
# ---------------------------------------------------------------------------

class TDD_BackNavigationGuard(TestCase):
    """
    TDD: Each exam page must include exam-guard.js and must NOT contain
    the old broken inline popstate handler that conflicted with script.js.
    """

    def setUp(self):
        self.client = Client()

    # -- homepage ----------------------------------------------------------

    def test_homepage_includes_exam_guard_script(self):
        status, html = _get_page(self.client, '/homepage/')
        self.assertEqual(status, 200)
        self.assertIn('exam-guard.js', html)

    def test_homepage_does_not_have_conflicting_inline_onpopstate(self):
        _, html = _get_page(self.client, '/homepage/')
        # Old broken handler: window.onpopstate = function () { history.go(1); }
        self.assertNotIn('history.go(1)', html)

    def test_homepage_still_includes_script_js(self):
        _, html = _get_page(self.client, '/homepage/')
        self.assertIn('script.js', html)

    # -- coding-theory -----------------------------------------------------

    def test_coding_theory_includes_exam_guard_script(self):
        status, html = _get_page(self.client, '/coding-theory/')
        self.assertEqual(status, 200)
        self.assertIn('exam-guard.js', html)

    def test_coding_theory_does_not_have_conflicting_inline_onpopstate(self):
        _, html = _get_page(self.client, '/coding-theory/')
        self.assertNotIn('history.go(1)', html)

    def test_coding_theory_still_includes_script_js(self):
        _, html = _get_page(self.client, '/coding-theory/')
        self.assertIn('script.js', html)

    # -- logic-reasoning ---------------------------------------------------

    def test_logic_reasoning_includes_exam_guard_script(self):
        status, html = _get_page(self.client, '/logic-reasoning/')
        self.assertEqual(status, 200)
        self.assertIn('exam-guard.js', html)

    def test_logic_reasoning_does_not_have_conflicting_inline_onpopstate(self):
        _, html = _get_page(self.client, '/logic-reasoning/')
        self.assertNotIn('history.go(1)', html)

    def test_logic_reasoning_still_includes_script_js(self):
        _, html = _get_page(self.client, '/logic-reasoning/')
        self.assertIn('script.js', html)

    # -- programming-task --------------------------------------------------

    def test_programming_task_includes_exam_guard_script(self):
        status, html = _get_page(self.client, '/programming-task/')
        self.assertEqual(status, 200)
        self.assertIn('exam-guard.js', html)

    def test_programming_task_does_not_have_conflicting_inline_onpopstate(self):
        _, html = _get_page(self.client, '/programming-task/')
        self.assertNotIn('history.go(1)', html)

    def test_programming_task_game_logic_still_present(self):
        """Verify that the problem content (coding platform logic) was not removed."""
        _, html = _get_page(self.client, '/programming-task/')
        self.assertIn('finishAssignment', html)


# ---------------------------------------------------------------------------
# TDD — exam-guard.js static file content
# ---------------------------------------------------------------------------

class TDD_ExamGuardFileContent(TestCase):
    """
    TDD: exam-guard.js must be served by Django and must contain the
    correct implementation for back-nav lock and tab-switch detection.
    """

    def setUp(self):
        self.client = Client()
        self.status, self.js = _get_static(self.client, '/static/exam-guard.js')

    def test_exam_guard_js_is_served(self):
        self.assertEqual(self.status, 200)

    def test_exam_guard_has_history_pushstate_for_back_lock(self):
        self.assertIn('history.pushState', self.js)

    def test_exam_guard_listens_for_popstate(self):
        self.assertIn('popstate', self.js)

    def test_exam_guard_blocks_alt_arrow_keys(self):
        self.assertIn('ArrowLeft', self.js)
        self.assertIn('ArrowRight', self.js)

    def test_exam_guard_blocks_mouse_back_forward_buttons(self):
        # buttons 3 and 4
        self.assertIn('e.button === 3', self.js)
        self.assertIn('e.button === 4', self.js)

    def test_exam_guard_listens_for_visibilitychange(self):
        self.assertIn('visibilitychange', self.js)

    def test_exam_guard_has_tab_switch_overlay(self):
        self.assertIn('tabWarningOverlay', self.js)

    def test_exam_guard_has_return_to_exam_button(self):
        self.assertIn('Return to Exam', self.js)

    def test_exam_guard_tracks_tab_switch_count(self):
        self.assertIn('tabSwitchCount', self.js)

    def test_exam_guard_stores_count_in_localstorage(self):
        self.assertIn('tabSwitchCount', self.js)
        self.assertIn('localStorage.setItem', self.js)

    def test_exam_guard_exposes_test_api(self):
        """exam-guard.js exposes window._examGuard for automated testing."""
        self.assertIn('_examGuard', self.js)

    def test_exam_guard_guard_is_iife(self):
        """Must be wrapped in an IIFE to avoid global scope pollution."""
        self.assertIn('(function', self.js)


# ---------------------------------------------------------------------------
# TDD — exam pages do NOT break other functionality
# ---------------------------------------------------------------------------

class TDD_ExamPagesFunctionalityIntact(TestCase):
    """
    TDD: Replacing the inline scripts must not remove the quiz questions
    or navigation buttons on each page.
    """

    def setUp(self):
        self.client = Client()

    def test_homepage_contains_ai_ml_questions(self):
        _, html = _get_page(self.client, '/homepage/')
        self.assertIn('AI/ML', html)
        # At least one question radio input
        self.assertIn('type="radio"', html)

    def test_homepage_has_next_button(self):
        _, html = _get_page(self.client, '/homepage/')
        self.assertIn("saveAndNext('homepage')", html)

    def test_coding_theory_contains_fullstack_questions(self):
        _, html = _get_page(self.client, '/coding-theory/')
        self.assertIn('Full Stack', html)
        self.assertIn('type="radio"', html)

    def test_coding_theory_has_next_button(self):
        _, html = _get_page(self.client, '/coding-theory/')
        self.assertIn("saveAndNext('coding-theory')", html)

    def test_logic_reasoning_contains_logic_questions(self):
        _, html = _get_page(self.client, '/logic-reasoning/')
        self.assertIn('Logic', html)
        self.assertIn('type="radio"', html)

    def test_logic_reasoning_has_next_button(self):
        _, html = _get_page(self.client, '/logic-reasoning/')
        self.assertIn("saveAndNext('logic-reasoning')", html)

    def test_programming_task_has_finish_button(self):
        _, html = _get_page(self.client, '/programming-task/')
        self.assertIn('finishAssignment', html)

    def test_programming_task_has_code_editor(self):
        _, html = _get_page(self.client, '/programming-task/')
        self.assertIn('id="editor"', html)


# ---------------------------------------------------------------------------
# BDD — Feature: Exam Integrity — Back Navigation Prevention
# ---------------------------------------------------------------------------

class BDD_Feature_BackNavigationPrevention(TestCase):
    """
    Feature: Back Navigation Prevention
      As an exam administrator
      I want students to be unable to navigate back to a previous section
      So that they cannot re-attempt completed sections

    The mechanism is implemented entirely in JavaScript (exam-guard.js +
    checkSectionAccess in script.js). These server-side BDD tests verify
    that the correct JS is delivered to every exam page.
    """

    def setUp(self):
        self.client = Client()

    def test_scenario_homepage_delivers_back_nav_guard(self):
        # GIVEN a student navigates to the AI/ML exam page
        # WHEN the page is loaded
        _, html = _get_page(self.client, '/homepage/')

        # THEN the page includes the back-navigation guard script
        self.assertIn('exam-guard.js', html)

        # AND the old broken handler is gone
        self.assertNotIn('history.go(1)', html)

    def test_scenario_coding_theory_delivers_back_nav_guard(self):
        # GIVEN a student navigates to Full Stack exam page
        _, html = _get_page(self.client, '/coding-theory/')
        self.assertIn('exam-guard.js', html)
        self.assertNotIn('history.go(1)', html)

    def test_scenario_logic_reasoning_delivers_back_nav_guard(self):
        # GIVEN a student navigates to Logic & Reasoning exam page
        _, html = _get_page(self.client, '/logic-reasoning/')
        self.assertIn('exam-guard.js', html)
        self.assertNotIn('history.go(1)', html)

    def test_scenario_programming_task_delivers_back_nav_guard(self):
        # GIVEN a student navigates to the Programming Challenge page
        _, html = _get_page(self.client, '/programming-task/')
        self.assertIn('exam-guard.js', html)
        self.assertNotIn('history.go(1)', html)

    def test_scenario_guard_uses_popstate_not_onpopstate_assignment(self):
        """
        GIVEN the guard script is loaded
        WHEN it is inspected
        THEN it uses addEventListener('popstate') not window.onpopstate = ...
        so it does not clobber other listeners
        """
        _, js = _get_static(self.client, '/static/exam-guard.js')
        # Must use addEventListener
        self.assertIn("addEventListener('popstate'", js)
        # Must NOT assign window.onpopstate directly
        self.assertNotIn('window.onpopstate', js)

    def test_scenario_guard_pushes_two_states_on_load(self):
        """
        GIVEN the guard is loaded
        THEN it calls history.pushState twice so there is always a forward
        entry to push back to
        """
        _, js = _get_static(self.client, '/static/exam-guard.js')
        count = js.count('history.pushState')
        # At least 2 pushState calls (load-time) + 1 inside popstate handler
        self.assertGreaterEqual(count, 3)


# ---------------------------------------------------------------------------
# BDD — Feature: Exam Integrity — Tab Switch Warning
# ---------------------------------------------------------------------------

class BDD_Feature_TabSwitchWarning(TestCase):
    """
    Feature: Tab Switch Warning
      As an exam administrator
      I want a visible warning to appear when a student switches tabs
      So that students are deterred from seeking outside help during the exam
    """

    def setUp(self):
        self.client = Client()
        _, self.js = _get_static(self.client, '/static/exam-guard.js')

    def test_scenario_warning_overlay_shown_on_tab_switch(self):
        # GIVEN the exam guard is loaded on an exam page
        # WHEN visibilitychange fires with document.hidden = true
        # THEN an overlay is shown (verified via JS source)
        self.assertIn('visibilitychange', self.js)
        self.assertIn('document.hidden', self.js)
        self.assertIn('showOverlay', self.js)

    def test_scenario_overlay_contains_do_not_switch_message(self):
        # GIVEN the overlay is created
        # THEN it displays a "Do Not Switch Tabs" warning
        self.assertIn('Do Not Switch Tabs', self.js)

    def test_scenario_overlay_shows_warning_count(self):
        # GIVEN a student switches tabs multiple times
        # THEN the overlay shows an incrementing warning counter
        self.assertIn('tabSwitchCount', self.js)
        self.assertIn('Warning ', self.js)

    def test_scenario_overlay_has_return_to_exam_button(self):
        # GIVEN the overlay is visible
        # WHEN the student returns to the tab and clicks the button
        # THEN the overlay is dismissed
        self.assertIn('Return to Exam', self.js)
        self.assertIn('hideOverlay', self.js)

    def test_scenario_tab_switch_count_persisted_to_localstorage(self):
        # GIVEN a student switches tabs
        # THEN the count is saved to localStorage for audit purposes
        self.assertIn("localStorage.setItem", self.js)
        self.assertIn("'tabSwitchCount'", self.js)

    def test_scenario_window_blur_also_triggers_warning(self):
        # GIVEN the student minimises the browser or alt-tabs
        # WHEN window blur fires
        # THEN the same warning overlay appears
        self.assertIn("window.addEventListener('blur'", self.js)

    def test_scenario_all_four_exam_pages_deliver_tab_switch_guard(self):
        # GIVEN a student is on any exam page
        # THEN all four pages include the tab-switch guard
        for url in ['/homepage/', '/coding-theory/', '/logic-reasoning/', '/programming-task/']:
            _, html = _get_page(self.client, url)
            self.assertIn('exam-guard.js', html,
                          msg=f'{url} does not include exam-guard.js')

    def test_scenario_exam_guard_does_not_block_normal_keyboard_input(self):
        """
        GIVEN the keyboard handler in exam-guard.js
        THEN it checks that the target is not an INPUT or TEXTAREA
        before blocking Backspace — so typing in answers still works
        """
        self.assertIn('TEXTAREA', self.js)
        self.assertIn('INPUT', self.js)
        # Must check inInput before blocking Backspace
        self.assertIn('inInput', self.js)
