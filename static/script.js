// Login functionality with validation
document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('loginForm');
    const togglePassword = document.getElementById('togglePassword');
    
    // Password toggle functionality
    if (togglePassword) {
        togglePassword.addEventListener('click', function() {
            const passwordField = document.getElementById('password');
            const type = passwordField.getAttribute('type') === 'password' ? 'text' : 'password';
            passwordField.setAttribute('type', type);
            this.classList.toggle('fa-eye');
            this.classList.toggle('fa-eye-slash');
        });
    }
    
    if (loginForm) {
        loginForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            
            // Validate email
            if (!validateEmail(email)) {
                showError('emailError', 'Please enter a valid email address');
                return;
            }
            
            // Validate password
            if (!validatePassword(password)) {
                showError('passwordError', 'Password must be 8-12 characters long');
                return;
            }
            
            // Clear errors
            clearErrors();
            
            // Authenticate user
            authenticateUser(email, password);
        });
    }
});

// Email validation
function validateEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

// Password validation
function validatePassword(password) {
    return password.length >= 8 && password.length <= 12;
}

// Show error message
function showError(elementId, message) {
    const errorElement = document.getElementById(elementId);
    errorElement.textContent = message;
}

// Clear all errors
function clearErrors() {
    document.getElementById('emailError').textContent = '';
    document.getElementById('passwordError').textContent = '';
}

// Authenticate user
async function authenticateUser(email, password) {
    try {
        const response = await fetch('/assignments/login/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ email: email, password: password })
        });
        
        const result = await response.json();
        
        if (result.success) {
            localStorage.setItem('currentUser', JSON.stringify({email: email}));
            localStorage.setItem('userEmail', email);
            localStorage.setItem('isLoggedIn', 'true');
            localStorage.setItem('loginTime', new Date().toISOString());
            window.location.href = '/dashboard/';
        } else {
            showError('passwordError', result.message || 'Invalid credentials');
        }
    } catch (error) {
        showError('passwordError', 'Login failed. Please check your connection.');
    }
}

// Save answers and navigate
function saveAndNext(currentPage) {
    const answers = {};
    const inputs = document.querySelectorAll('input[type="radio"]:checked');
    
    inputs.forEach(input => {
        answers[input.name] = input.value;
    });
    
    if (Object.keys(answers).length === 0) {
        alert('Please answer at least one question before proceeding.');
        return;
    }
    
    // Calculate score
    const score = calculateScore(currentPage, answers);
    
    // Save to localStorage
    const existingData = JSON.parse(localStorage.getItem('assignmentData') || '{}');
    existingData[currentPage] = {
        answers: answers,
        score: score,
        timestamp: new Date().toISOString(),
        completed: true
    };
    localStorage.setItem('assignmentData', JSON.stringify(existingData));
    
    // Mark section as locked ONLY after completion
    lockSection(currentPage);
    
    // Clear timer
    if (examTimer) {
        clearInterval(examTimer);
    }
    
    // Navigate to next page
    if (currentPage === 'homepage') {
        window.location.href = '/coding-theory/';
    } else if (currentPage === 'coding-theory') {
        window.location.href = '/logic-reasoning/';
    } else if (currentPage === 'logic-reasoning') {
        window.location.href = '/programming-task/';
    }
}

// Lock completed sections
function lockSection(sectionName) {
    const lockedSections = JSON.parse(localStorage.getItem('lockedSections') || '[]');
    if (!lockedSections.includes(sectionName)) {
        lockedSections.push(sectionName);
        localStorage.setItem('lockedSections', JSON.stringify(lockedSections));
    }
}

// Clear all locks (for testing/reset)
function clearAllLocks() {
    localStorage.removeItem('lockedSections');
    localStorage.removeItem('assignmentData');
    console.log('All section locks cleared');
}

// Reset student data (for new student testing)
function resetStudentData() {
    localStorage.clear();
    console.log('All student data cleared - ready for new student');
    window.location.href = '/dashboard/';
}

// Debug function to check current state
function checkCurrentState() {
    console.log('Current assignment data:', JSON.parse(localStorage.getItem('assignmentData') || '{}'));
    console.log('Current page:', window.location.pathname);
}

// Check if section is locked - redirect to dashboard if already completed
function checkSectionAccess() {
    const lockedSections = JSON.parse(localStorage.getItem('lockedSections') || '[]');
    const currentPage = window.location.pathname.replace(/\//g, '') || 'homepage';

    if (lockedSections.includes(currentPage)) {
        // Section already completed - send back to dashboard
        window.location.replace('/dashboard/');
        return false;
    }

    // Push a history state so the back button stays on this page
    history.pushState({ page: currentPage }, '', window.location.href);

    window.addEventListener('popstate', function() {
        // When back/forward is pressed, push the state again to prevent leaving
        history.pushState({ page: currentPage }, '', window.location.href);
    });

    return true;
}

// Calculate score for MCQs
function calculateScore(page, answers) {
    const correctAnswers = {
        homepage: {
            q1: 'Naive Bayes', q2: 'Reduction in entropy', q3: 'Curse of dimensionality',
            q4: 'F1-score', q5: 'Both a & c', q6: 'Reward', q7: 'Prevent exploding gradients',
            q8: 'DBSCAN', q9: 'RNN', q10: 'Dimensionality reduction', q11: 'Bootstrapped data sample',
            q12: 'Sparse models', q13: 'Random Forest', q14: 'True Positive Rate vs False Positive Rate',
            q15: 'Variance'
        },
        'coding-theory': {
            ct1: 'useEffect', ct2: '401', ct3: 'Document Store', ct4: 'fs', ct5: 'SELECT DISTINCT',
            ct6: 'PUSH', ct7: 'REST API and backend routing', ct8: '27017', ct9: 'z-index',
            ct10: 'a & c', ct11: 'npm init', ct12: 'Key referencing another table\'s primary key',
            ct13: 'Context API', ct14: 'Angular', ct15: 'Stateless'
        },
        'logic-reasoning': {
            lr1: '6 days', lr2: '30', lr3: '1000', lr4: '144', lr5: '12:16',
            lr6: '3', lr7: '2 hr', lr8: '144', lr9: '6 days', lr10: '3 km/h',
            lr11: '24', lr12: '8', lr13: '112', lr14: '5/3', lr15: '18,000',
            lr16: '243', lr17: '8:15', lr18: 'Chair', lr19: 'Three intersecting circles',
            lr20: 'All of these'
        }
    };
    
    if (!correctAnswers[page]) return 0;
    
    let score = 0;
    const total = Object.keys(correctAnswers[page]).length;
    
    Object.entries(correctAnswers[page]).forEach(([key, correct]) => {
        if (answers[key] === correct) score++;
    });
    
    return { correct: score, total: total, percentage: Math.round((score/total) * 100) };
}

// Language templates
const languageTemplates = {
    javascript: {
        template: 'function factorial(n) {\n    // Write your factorial logic here\n    // Example: Use loop or recursion\n    // factorial(5) should return 120\n}',
        description: 'Write a JavaScript function that calculates factorial. Test will check factorial(5) = 120'
    },
    python: {
        template: 'def factorial(n):\n    # Write your factorial logic here\n    # Use loop: for i in range(1, n+1)\n    # Or recursion: return n * factorial(n-1) if n > 1 else 1\n    pass',
        description: 'Write a Python function that calculates factorial. Use loop or recursion.'
    },
    java: {
        template: 'public static int factorial(int n) {\n    // Write your factorial logic here\n    // Use loop or recursion\n    // factorial(5) should return 120\n    return 0;\n}',
        description: 'Write a Java method that calculates factorial using loop or recursion.'
    },
    cpp: {
        template: 'int factorial(int n) {\n    // Write your factorial logic here\n    // Use for loop or recursion\n    // factorial(5) should return 120\n    return 0;\n}',
        description: 'Write a C++ function that calculates factorial using loop or recursion.'
    },
    c: {
        template: 'int factorial(int n) {\n    // Write your factorial logic here\n    // Use for loop or recursion\n    // factorial(5) should return 120\n    return 0;\n}',
        description: 'Write a C function that calculates factorial using loop or recursion.'
    },
    csharp: {
        template: 'public static int Factorial(int n) {\n    // Write your factorial logic here\n    // Use for loop or recursion\n    // Factorial(5) should return 120\n    return 0;\n}',
        description: 'Write a C# method that calculates factorial using loop or recursion.'
    },
    php: {
        template: 'function factorial($n) {\n    // Write your factorial logic here\n    // Use for loop or recursion\n    // factorial(5) should return 120\n}',
        description: 'Write a PHP function that calculates factorial using loop or recursion.'
    },
    ruby: {
        template: 'def factorial(n)\n    # Write your factorial logic here\n    # Use loop or recursion\n    # factorial(5) should return 120\nend',
        description: 'Write a Ruby method that calculates factorial using loop or recursion.'
    }
};

// Set Python template (no language selection needed)
function setPythonTemplate() {
    const codeEditor = document.getElementById('codeEditor');
    if (codeEditor && !codeEditor.value.trim()) {
        codeEditor.value = languageTemplates.python.template;
    }
}

// Test code functionality
async function testCode() {
    const code = document.getElementById('codeEditor').value;
    const language = 'python';
    const output = document.getElementById('output');
    
    output.innerHTML = '<span style="color: #007bff;">Testing code...</span>';
    
    try {
        const response = await fetch('/api/test-code/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ code: code, language: language })
        });
        
        const result = await response.json();
        
        if (result.success) {
            const score = Math.round(result.score);
            let resultHtml = `<div class="test-results">`;
            resultHtml += `<div class="score">Score: ${score}% (${result.message})</div>`;
            
            if (result.results) {
                resultHtml += `<div class="test-cases">`;
                result.results.forEach((test, index) => {
                    const status = test.passed ? '✅' : '❌';
                    const color = test.passed ? '#28a745' : '#dc3545';
                    resultHtml += `<div style="color: ${color}; margin: 5px 0;">`;
                    resultHtml += `${status} Test ${index + 1}: factorial(${test.input}) = ${test.output} (expected: ${test.expected})`;
                    resultHtml += `</div>`;
                });
                resultHtml += `</div>`;
            }
            
            resultHtml += `</div>`;
            output.innerHTML = resultHtml;
            return score >= 60; // Pass if 60% or more
        } else {
            output.innerHTML = `<span class="error">❌ ${result.message}</span>`;
            return false;
        }
    } catch (error) {
        output.innerHTML = `<span class="error">❌ Error: ${error.message}</span>`;
        return false;
    }
}

// Check if code contains basic factorial logic
function checkFactorialLogic(code, language) {
    const lowerCode = code.toLowerCase();
    
    // Check for basic factorial patterns
    const hasLoop = lowerCode.includes('for') || lowerCode.includes('while');
    const hasRecursion = lowerCode.includes('factorial') && (lowerCode.includes('return') || lowerCode.includes('*'));
    const hasMultiplication = lowerCode.includes('*');
    const hasBaseCase = lowerCode.includes('1') || lowerCode.includes('0');
    
    // Language-specific checks
    switch(language) {
        case 'python':
            return (hasLoop || hasRecursion) && hasMultiplication;
        case 'java':
        case 'cpp':
        case 'c':
            return (hasLoop || hasRecursion) && hasMultiplication && lowerCode.includes('int');
        case 'csharp':
            return (hasLoop || hasRecursion) && hasMultiplication;
        default:
            return hasMultiplication && (hasLoop || hasRecursion);
    }
}

// Submit programming task (FINAL SUBMISSION)
async function submitTask() {
    console.log('Final submit task called');
    
    const code = document.getElementById('codeEditor').value;
    const language = 'python';
    
    // Simple validation
    if (!code.trim()) {
        const proceed = confirm('No code written. Submit anyway?');
        if (!proceed) return;
    }
    
    try {
        // Save programming task data
        const existingData = JSON.parse(localStorage.getItem('assignmentData') || '{}');
        existingData['programming-task'] = {
            code: code || '# No code submitted',
            language: language,
            score: { correct: code.trim() ? 1 : 0, total: 1, percentage: code.trim() ? 80 : 0 },
            timestamp: new Date().toISOString(),
            completed: true
        };
        localStorage.setItem('assignmentData', JSON.stringify(existingData));
        
        // Clear timer
        if (examTimer) {
            clearInterval(examTimer);
        }
        
        // Submit ALL data to server (final submission)
        await submitToServer();
        
    } catch (error) {
        console.error('Error in submitTask:', error);
        alert('Error submitting assignment: ' + error.message);
    }
}

// Submit data to server
async function submitToServer() {
    const data = JSON.parse(localStorage.getItem('assignmentData') || '{}');
    const currentUser = JSON.parse(localStorage.getItem('currentUser') || '{}');
    const userEmail = currentUser.email || localStorage.getItem('userEmail');
    
    const submissionData = {
        student: userEmail,
        loginTime: localStorage.getItem('loginTime') || new Date().toISOString(),
        submissionTime: new Date().toISOString(),
        results: data,
        totalScore: calculateTotalScore(data)
    };
    
    try {
        const response = await fetch('/assignments/submit/', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify(submissionData)
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert('Assignment successfully submitted! Thank you for completing the assessment.');
            localStorage.removeItem('assignmentData');
            localStorage.removeItem('lockedSections');
            window.location.href = '/dashboard/';
        } else {
            alert('Error submitting assignment: ' + result.message);
        }
        
    } catch (error) {
        console.log('Error occurred:', error);
        alert('Error submitting assignment. Please try again.');
    }
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

// Calculate total score
function calculateTotalScore(data) {
    let totalCorrect = 0;
    let totalQuestions = 0;
    
    Object.values(data).forEach(section => {
        if (section.score) {
            totalCorrect += section.score.correct;
            totalQuestions += section.score.total;
        }
    });
    
    return {
        correct: totalCorrect,
        total: totalQuestions,
        percentage: totalQuestions > 0 ? Math.round((totalCorrect/totalQuestions) * 100) : 0
    };
}

// Timer functionality
let examTimer;
let timeRemaining;

function startTimer(minutes) {
    timeRemaining = minutes * 60; // Convert to seconds
    const timerElement = document.getElementById('timer');
    
    examTimer = setInterval(() => {
        const mins = Math.floor(timeRemaining / 60);
        const secs = timeRemaining % 60;
        
        timerElement.textContent = `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
        
        // Warning at 5 minutes
        if (timeRemaining <= 300 && timeRemaining > 60) {
            timerElement.className = 'warning';
        }
        // Critical at 1 minute
        else if (timeRemaining <= 60) {
            timerElement.className = 'critical';
        }
        
        if (timeRemaining <= 0) {
            clearInterval(examTimer);
            timeExpired();
        }
        
        timeRemaining--;
    }, 1000);
}

function timeExpired() {
    const currentPage = window.location.pathname.split('/')[1] || 'homepage';
    
    // Disable all form elements
    const inputs = document.querySelectorAll('input, button, textarea, select');
    inputs.forEach(input => input.disabled = true);
    
    // Show time expired message
    alert('⏰ Time is up! Assignment closed. Moving to next stage...');
    
    // Auto-submit current answers
    setTimeout(() => {
        if (currentPage === 'programming-task') {
            submitTask();
        } else {
            // Save whatever answers were selected
            const answers = {};
            const checkedInputs = document.querySelectorAll('input[type="radio"]:checked');
            checkedInputs.forEach(input => {
                answers[input.name] = input.value;
            });
            
            // Calculate score for answered questions
            const score = calculateScore(currentPage, answers);
            
            // Save to localStorage
            const existingData = JSON.parse(localStorage.getItem('assignmentData') || '{}');
            existingData[currentPage] = {
                answers: answers,
                score: score,
                timestamp: new Date().toISOString(),
                completed: true,
                timeExpired: true
            };
            localStorage.setItem('assignmentData', JSON.stringify(existingData));
            
            // Lock section and navigate
            lockSection(currentPage);
            
            if (currentPage === 'homepage') {
                window.location.href = '/coding-theory/';
            } else if (currentPage === 'coding-theory') {
                window.location.href = '/logic-reasoning/';
            } else if (currentPage === 'logic-reasoning') {
                window.location.href = '/programming-task/';
            }
        }
    }, 2000); // 2 second delay for user to read message
}



// Load saved data on page load (for resuming)
document.addEventListener('DOMContentLoaded', function() {
    const savedData = JSON.parse(localStorage.getItem('assignmentData') || '{}');
    const currentPage = window.location.pathname.split('/')[1] || 'homepage';
    
    // Don't pre-load answers - keep questions clean for students
    // if (savedData[currentPage] && savedData[currentPage].answers) {
    //     Object.entries(savedData[currentPage].answers).forEach(([name, value]) => {
    //         const input = document.querySelector(`input[name="${name}"][value="${value}"]`);
    //         if (input) input.checked = true;
    //     });
    // }
    
    // Load programming task code and language
    if (currentPage === 'programming-task') {
        const codeEditor = document.getElementById('codeEditor');
        
        // Always start with clean template - don't pre-load saved code
        setPythonTemplate();
    }
    
    // Check section access and start timer
    if (checkSectionAccess()) {
        if (currentPage === 'homepage') {
            startTimer(18); // 18 minutes for AI/ML
        } else if (currentPage === 'coding-theory') {
            startTimer(18); // 18 minutes for Full Stack
        } else if (currentPage === 'logic-reasoning') {
            startTimer(24); // 24 minutes for Logic & Reasoning
        } else if (currentPage === 'programming-task') {
            // No timer for programming task - unlimited time
            const timerElement = document.getElementById('timer');
            if (timerElement) {
                timerElement.textContent = 'No Time Limit';
            }
        }
    }
});