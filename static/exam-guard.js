/**
 * exam-guard.js
 * Loaded on every exam page (homepage, coding-theory, logic-reasoning, programming-task).
 *
 * Responsibilities:
 *  1. Back-navigation lock  – browser back/forward buttons stay on this page.
 *  2. Tab-switch warning    – when the student switches to another tab or
 *                             minimises the window, a non-dismissible overlay
 *                             appears until they return, and a counter tracks
 *                             how many times it happened.
 */

(function () {
    'use strict';

    // ------------------------------------------------------------------ //
    // 1. BACK / FORWARD NAVIGATION LOCK
    // ------------------------------------------------------------------ //
    // Push two states so there is always a "forward" entry to jump to.
    history.pushState({ examPage: true }, '', location.href);
    history.pushState({ examPage: true }, '', location.href);

    window.addEventListener('popstate', function () {
        // Whenever the user presses Back or Forward, push a fresh state
        // so the URL never actually changes.
        history.pushState({ examPage: true }, '', location.href);
    });

    // Block Alt+Left / Alt+Right, Backspace (outside inputs), F5, Ctrl+R
    document.addEventListener('keydown', function (e) {
        var tag = e.target.tagName;
        var inInput = (tag === 'INPUT' || tag === 'TEXTAREA');

        if (
            (e.altKey && (e.key === 'ArrowLeft' || e.key === 'ArrowRight')) ||
            (e.key === 'Backspace' && !inInput) ||
            e.key === 'F5' ||
            (e.ctrlKey && e.key === 'r')
        ) {
            e.preventDefault();
            return false;
        }
    });

    // Block mouse back / forward buttons (buttons 3 and 4)
    document.addEventListener('mousedown', function (e) {
        if (e.button === 3 || e.button === 4) {
            e.preventDefault();
            return false;
        }
    });

    // ------------------------------------------------------------------ //
    // 2. TAB-SWITCH / WINDOW BLUR WARNING
    // ------------------------------------------------------------------ //
    var tabSwitchCount = 0;
    var overlay = null;

    function createOverlay() {
        if (overlay) return; // already created

        overlay = document.createElement('div');
        overlay.id = 'tabWarningOverlay';
        overlay.style.cssText = [
            'position:fixed',
            'top:0', 'left:0',
            'width:100%', 'height:100%',
            'background:rgba(0,0,0,0.85)',
            'z-index:999999',
            'display:flex',
            'align-items:center',
            'justify-content:center',
            'flex-direction:column',
        ].join(';');

        var box = document.createElement('div');
        box.style.cssText = [
            'background:#fff',
            'border-radius:12px',
            'padding:40px 50px',
            'text-align:center',
            'max-width:480px',
            'box-shadow:0 8px 32px rgba(0,0,0,0.4)',
        ].join(';');

        var icon = document.createElement('div');
        icon.textContent = '⚠️';
        icon.style.cssText = 'font-size:56px;margin-bottom:16px;';

        var title = document.createElement('h2');
        title.textContent = 'Do Not Switch Tabs!';
        title.style.cssText = 'margin:0 0 12px;color:#dc3545;font-size:24px;';

        var msg = document.createElement('p');
        msg.id = 'tabWarningMsg';
        msg.style.cssText = 'margin:0 0 24px;color:#333;font-size:16px;line-height:1.5;';

        var btn = document.createElement('button');
        btn.textContent = 'Return to Exam';
        btn.style.cssText = [
            'background:#28a745',
            'color:#fff',
            'border:none',
            'padding:12px 32px',
            'border-radius:6px',
            'font-size:16px',
            'cursor:pointer',
            'font-weight:bold',
        ].join(';');
        btn.addEventListener('click', hideOverlay);

        box.appendChild(icon);
        box.appendChild(title);
        box.appendChild(msg);
        box.appendChild(btn);
        overlay.appendChild(box);
        document.body.appendChild(overlay);
    }

    function showOverlay() {
        tabSwitchCount += 1;
        createOverlay();
        var msg = document.getElementById('tabWarningMsg');
        if (msg) {
            msg.innerHTML =
                'You switched away from the exam tab.<br>' +
                '<strong>Warning ' + tabSwitchCount + '</strong>: ' +
                'Repeated tab switching may result in your exam being flagged.<br>' +
                'Please return to the exam immediately.';
        }
        overlay.style.display = 'flex';
        // Store count in localStorage for potential server-side audit
        localStorage.setItem('tabSwitchCount', tabSwitchCount);
    }

    function hideOverlay() {
        if (overlay) {
            overlay.style.display = 'none';
        }
    }

    // Trigger when the page loses focus (tab switch, alt-tab, minimise)
    document.addEventListener('visibilitychange', function () {
        if (document.hidden) {
            showOverlay();
        }
    });

    // Additional fallback for window blur
    window.addEventListener('blur', function () {
        if (document.hidden) return; // already handled by visibilitychange
        showOverlay();
    });

    // When focus returns, keep overlay visible until student clicks "Return"
    // (the button is the only way to dismiss it)

    // Expose for testing
    window._examGuard = {
        getTabSwitchCount: function () { return tabSwitchCount; },
        simulateTabSwitch: showOverlay,
        simulateReturn: hideOverlay,
        isOverlayVisible: function () {
            return overlay !== null && overlay.style.display !== 'none';
        },
    };
})();
