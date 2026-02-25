// Global variables
let isLoggedIn = false;

// Initialize page
document.addEventListener('DOMContentLoaded', function() {
    console.log("✅ auth.js loaded, DOM ready");
    setupEventListeners();
    
    // Show appropriate form based on URL parameters or path
    const urlParams = new URLSearchParams(window.location.search);
    const currentPath = window.location.pathname;

    // ✅ Default: show login at root "/"
    if (urlParams.get('register') === 'true' || currentPath === '/register/') {
        switchToRegister();
    } else {
        switchToLogin();
    }
});

// Setup event listeners
function setupEventListeners() {
    console.log("✅ Setting up event listeners...");

    const loginTab = document.getElementById('loginTab');
    const registerTab = document.getElementById('registerTab');
    const showRegisterLink = document.getElementById('showRegisterLink');
    const showLoginLink = document.getElementById('showLoginLink');
    
    if (loginTab) loginTab.addEventListener('click', () => switchToLogin());
    if (registerTab) registerTab.addEventListener('click', () => switchToRegister());
    if (showRegisterLink) {
        showRegisterLink.addEventListener('click', (e) => {
            e.preventDefault();
            console.log("➡️ Register link clicked");
            switchToRegister();
        });
    }
    if (showLoginLink) {
        showLoginLink.addEventListener('click', (e) => {
            e.preventDefault();
            console.log("➡️ Login link clicked");
            switchToLogin();
        });
    }
    
    // Dropdown toggles
    const streamInput = document.getElementById('streamInput');
    const collegeInput = document.getElementById('collegeRegInput');
    
    if (streamInput) {
        streamInput.addEventListener('click', () => toggleDropdown('streamDropdown'));
    }
    if (collegeInput) {
        collegeInput.addEventListener('click', () => toggleDropdown('collegeRegDropdown'));
    }
    
    // Password toggles
    const toggleBtn = document.getElementById('toggleBtn');
    const registerToggleBtn = document.getElementById('registerToggleBtn');
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');
    
    if (toggleBtn) toggleBtn.addEventListener('click', () => togglePassword('passwordInput'));
    if (registerToggleBtn) registerToggleBtn.addEventListener('click', () => togglePassword('registerPassword'));
    
    // Form submissions
    if (loginForm) loginForm.addEventListener('submit', handleLogin);
    if (registerForm) registerForm.addEventListener('submit', handleRegister);
}

// Switch to login
function switchToLogin() {
    const loginTab = document.getElementById('loginTab');
    const registerTab = document.getElementById('registerTab');
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');
    const formTitle = document.getElementById('formTitle');

    if (loginTab) loginTab.classList.add('active');
    if (registerTab) registerTab.classList.remove('active');
    if (loginForm) loginForm.style.display = 'block';
    if (registerForm) registerForm.style.display = 'none';
    if (formTitle) formTitle.textContent = 'Login Form';

    // Clear register form
    if (registerForm) {
        const inputs = registerForm.querySelectorAll('input');
        inputs.forEach(input => {
            if (input.type !== 'button') {
                input.value = '';
            }
        });
    }

    // Clear dropdown values
    const streamInputEl = document.getElementById('streamInput');
    if (streamInputEl) streamInputEl.value = '';
    const collegeRegEl = document.getElementById('collegeRegInput');
    if (collegeRegEl) collegeRegEl.value = '';

    // Clear login form
    if (loginForm && typeof loginForm.reset === 'function') {
        loginForm.reset();
    }
}

// Switch to register
function switchToRegister() {
    const loginTab = document.getElementById('loginTab');
    const registerTab = document.getElementById('registerTab');
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');
    const formTitle = document.getElementById('formTitle');

    if (loginTab) loginTab.classList.remove('active');
    if (registerTab) registerTab.classList.add('active');
    if (loginForm) loginForm.style.display = 'none';
    if (registerForm) registerForm.style.display = 'block';
    if (formTitle) formTitle.textContent = 'Register Form';

    // Clear login form
    if (loginForm && typeof loginForm.reset === 'function') {
        loginForm.reset();
    }

    // Clear register form fields
    if (registerForm) {
        const inputs = registerForm.querySelectorAll('input');
        inputs.forEach(input => {
            if (input.type !== 'button') {
                input.value = '';
            }
        });
    }

    // Clear dropdown values
    const streamInputEl = document.getElementById('streamInput');
    if (streamInputEl) streamInputEl.value = '';
    const collegeRegEl = document.getElementById('collegeRegInput');
    if (collegeRegEl) collegeRegEl.value = '';
}

// Toggle dropdown
function toggleDropdown(dropdownId) {
    const dropdown = document.getElementById(dropdownId);
    if (dropdown) {
        document.querySelectorAll('.dropdown').forEach(d => {
            if (d.id !== dropdownId) {
                d.classList.remove('show');
            }
        });
        dropdown.classList.toggle('show');
    }
}

// Select stream
function selectStream(stream) {
    const streamInput = document.getElementById('streamInput');
    const streamDropdown = document.getElementById('streamDropdown');
    if (streamInput) streamInput.value = stream;
    if (streamDropdown) streamDropdown.classList.remove('show');
}

// Select stream
function selectStream(stream) {
    const streamInput = document.getElementById('streamInput');
    const streamDropdown = document.getElementById('streamDropdown');
    if (streamInput) streamInput.value = stream;
    if (streamDropdown) streamDropdown.classList.remove('show');
}

// Select college
function selectCollege(college) {
    const collegeInput = document.getElementById('collegeRegInput');
    const collegeDropdown = document.getElementById('collegeRegDropdown');
    if (collegeInput) collegeInput.value = college;
    if (collegeDropdown) collegeDropdown.classList.remove('show');
}



// Toggle password visibility
function togglePassword(inputId) {
    const input = document.getElementById(inputId);
    const button = input.nextElementSibling;
    
    if (input && input.type === 'password') {
        input.type = 'text';
        if (button) button.textContent = '🙈';
    } else if (input) {
        input.type = 'password';
        if (button) button.textContent = '👁';
    }
}

// Handle login
function handleLogin(e) {
    e.preventDefault();
    const formData = new FormData(e.target);
    const email = formData.get('email');
    const password = formData.get('password');
    
    if (!email || !password) {
        showErrorMessage('Please enter both email and password');
        return;
    }
    
    fetch('/assignments/login/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({ email, password })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            localStorage.setItem('currentUser', JSON.stringify({ email }));
            localStorage.setItem('userEmail', email);
            localStorage.setItem('isLoggedIn', 'true');
            localStorage.setItem('loginTime', new Date().toISOString());
            window.location.href = '/dashboard/';
        } else {
            showErrorMessage('Invalid email or password');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showErrorMessage('Login failed. Please check your connection.');
    });
}

// Handle register
function handleRegister(e) {
    e.preventDefault();
    console.log('DEBUG: Registration form submitted');
    
    const formData = new FormData(e.target);
    const name = formData.get('name');
    const email = formData.get('email');
    const mobile = formData.get('mobile');
    const roll_number = formData.get('roll_number');
    const stream = formData.get('stream');
    const skills = formData.get('skills');
    const college = formData.get('college');
    const ssc_grade = formData.get('ssc_grade');
    const intermediate_grade = formData.get('intermediate_grade');
    const current_semester_cgpa = formData.get('current_semester_cgpa');
    const password = formData.get('password');
    
    console.log('Form data:', { name, email, mobile, roll_number, stream, skills, college, ssc_grade, intermediate_grade, current_semester_cgpa });
    
    if (!name || !email || !mobile || !roll_number || !stream || !skills || !college || !ssc_grade || !intermediate_grade || !current_semester_cgpa || !password) {
        showErrorMessage('Please fill in all required fields');
        return;
    }
    
    const csrfToken = getCookie('csrftoken') || document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    console.log('CSRF Token:', csrfToken);
    
    const requestData = {
        name, email, mobile, roll_number, stream, skills,
        college_name: college,
        ssc_grade, intermediate_grade, current_semester_cgpa, password
    };
    
    console.log('Sending request data:', requestData);
    
    fetch('/assignments/register/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify(requestData)
    })
    .then(response => {
        console.log('Response status:', response.status);
        if (!response.ok) {
            return response.text().then(text => {
                console.log('Error response:', text);
                throw new Error(`HTTP ${response.status}: ${text}`);
            });
        }
        return response.json();
    })
    .then(data => {
        console.log('Response data:', data);
        if (data.success) {
            alert('✅ Registration successful! Redirecting to login...');
            setTimeout(() => {
                switchToLogin();
                const emailInput = document.querySelector('#loginForm input[name="email"]');
                if (emailInput) {
                    emailInput.value = email;
                }
            }, 1000);
        } else {
            showErrorMessage('Registration failed: ' + data.message);
        }
    })
    .catch(error => {
        console.error('DEBUG: Registration error:', error);
        showErrorMessage('Registration failed: ' + error.message);
    });
}

// Get CSRF token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Close dropdowns when clicking outside
document.addEventListener('click', function(e) {
    if (!e.target.closest('.input-wrap')) {
        document.querySelectorAll('.dropdown').forEach(dropdown => {
            dropdown.classList.remove('show');
        });
    }
});

// Error message handling
function showErrorMessage(message) {
    let errorDiv = document.getElementById('errorMessage');
    if (!errorDiv) {
        errorDiv = document.createElement('div');
        errorDiv.id = 'errorMessage';
        errorDiv.style.cssText = 'color: #dc3545; background: #f8d7da; border: 1px solid #f5c6cb; padding: 10px; margin: 10px 0; border-radius: 4px; font-size: 14px;';
        
        const authBox = document.getElementById('authBox');
        if (authBox) {
            authBox.insertBefore(errorDiv, authBox.firstChild);
        }
    }
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';
    
    setTimeout(() => {
        if (errorDiv) {
            errorDiv.style.display = 'none';
        }
    }, 5000);
}

function clearErrorMessages() {
    const errorDiv = document.getElementById('errorMessage');
    if (errorDiv) {
        errorDiv.style.display = 'none';
    }
}

// Utility functions for notifications
function showSuccess(message) {
    alert('✅ ' + message);
}

function showError(message) {
    alert('❌ ' + message);
}

