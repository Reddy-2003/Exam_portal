// Check authentication on page load
document.addEventListener('DOMContentLoaded', function() {
    checkAuthentication();
    loadUserData();
    checkAssignmentStatus();
    checkExamStatus();
});

function checkAuthentication() {
    const isLoggedIn = localStorage.getItem('isLoggedIn');
    const currentUser = localStorage.getItem('currentUser');
    
    if (!isLoggedIn || !currentUser) {
        // Redirect to login if not authenticated
        window.location.href = '/login/';
        return;
    }
}

function loadUserData() {
    const currentUser = JSON.parse(localStorage.getItem('currentUser') || '{}');
    const userEmail = currentUser.email || 'Guest';
    
    // Display user email in dashboard
    const emailElement = document.getElementById('studentEmail');
    if (emailElement) {
        emailElement.textContent = userEmail;
    }
}

function checkAssignmentStatus() {
    const currentUser = JSON.parse(localStorage.getItem('currentUser') || '{}');
    const userEmail = currentUser.email;
    
    if (!userEmail) return;
    
    // Fetch current status from backend
    fetch('/assignments/student-status/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({ email: userEmail })
    })
    .then(response => response.json())
    .then(data => {
        console.log('Status data:', data); // Debug log
        updateStageStatus('assignment', data.assignment_status, 'assignmentStatus', 'stage1');
        updateStageStatus('group_discussion', data.group_discussion_status, 'gdStatus', 'stage2');
        updateStageStatus('technical', data.technical_status, 'technicalStatus', 'stage3');
        updateStageStatus('hr_round', data.hr_status, 'hrStatus', 'stage4');
        
        updateProgressMessage(data);
        updateActionButton(data);

        // If student hasn't started yet, clear any stale exam localStorage
        // so checkSectionAccess() on homepage doesn't wrongly redirect them
        if (data.assignment_status === 'pending') {
            localStorage.removeItem('lockedSections');
            localStorage.removeItem('assignmentData');
        }
    })
    .catch(error => {
        console.error('Error fetching status:', error);
    });
}

function updateStageStatus(stage, status, statusElementId, stageElementId) {
    console.log(`Updating ${stage} status to: ${status}`); // Debug log
    const statusEl = document.getElementById(statusElementId);
    const stageEl = document.getElementById(stageElementId);
    
    // Reset classes
    stageEl.classList.remove('completed', 'failed', 'active', 'submitted');
    
    switch(status) {
        case 'pending':
            statusEl.textContent = 'Pending';
            statusEl.className = 'stage-status pending';
            break;
        case 'in_progress':
            statusEl.textContent = 'Ready to Start';
            statusEl.className = 'stage-status active';
            stageEl.classList.add('active');
            break;
        case 'completed':
            statusEl.textContent = 'Submitted - Awaiting Review';
            statusEl.className = 'stage-status submitted';
            stageEl.classList.add('submitted');
            break;
        case 'qualified':
            statusEl.textContent = 'Qualified';
            statusEl.className = 'stage-status qualified';
            stageEl.classList.add('completed');
            break;
        case 'rejected':
            statusEl.textContent = 'Rejected';
            statusEl.className = 'stage-status rejected';
            stageEl.classList.add('failed');
            break;
    }
}

function updateProgressMessage(data) {
    const messageText = document.getElementById('messageText');
    const progressMessage = document.getElementById('progressMessage');
    
    // Check for rejection at any stage
    if (data.assignment_status === 'rejected') {
        progressMessage.className = 'progress-message error';
        messageText.innerHTML = '❌ Assignment not qualified. Interview process ended.';
        return;
    }
    if (data.group_discussion_status === 'rejected') {
        progressMessage.className = 'progress-message error';
        messageText.innerHTML = '❌ Group Discussion not qualified. Interview process ended.';
        return;
    }
    if (data.technical_status === 'rejected') {
        progressMessage.className = 'progress-message error';
        messageText.innerHTML = '❌ Technical Round not qualified. Interview process ended.';
        return;
    }
    if (data.hr_status === 'rejected') {
        progressMessage.className = 'progress-message error';
        messageText.innerHTML = '❌ HR Round not qualified. Interview process ended.';
        return;
    }
    
    // Success messages
    if (data.hr_status === 'qualified') {
        progressMessage.className = 'progress-message success';
        messageText.innerHTML = '🎉 You are selected. Further information will reach your department.';
    } else if (data.hr_status === 'in_progress') {
        progressMessage.className = 'progress-message info';
        messageText.innerHTML = '🎆 You are selected for HR Round.';
    } else if (data.technical_status === 'in_progress') {
        progressMessage.className = 'progress-message info';
        messageText.innerHTML = '💻 You are selected for Technical Round.';
    } else if (data.group_discussion_status === 'in_progress') {
        progressMessage.className = 'progress-message info';
        messageText.innerHTML = '💬 You are selected for Group Discussion.';
    } else if (data.assignment_status === 'completed') {
        progressMessage.className = 'progress-message info';
        messageText.innerHTML = '⏳ Assignment submitted. Awaiting review.';
    } else {
        progressMessage.className = 'progress-message';
        messageText.innerHTML = 'Ready to begin your interview process';
    }
}

function updateActionButton(data) {
    const startBtn = document.getElementById('startAssignmentBtn');
    
    // Hide button if any stage is rejected or if all completed
    if (data.assignment_status === 'rejected' || 
        data.group_discussion_status === 'rejected' || 
        data.technical_status === 'rejected' || 
        data.hr_status === 'rejected' ||
        data.hr_status === 'qualified') {
        startBtn.style.display = 'none';
        return;
    }
    
    // Show appropriate button based on current stage
    if (data.assignment_status === 'pending' || data.assignment_status === 'in_progress') {
        startBtn.textContent = 'Start Assignment';
        startBtn.style.display = '';
        startBtn.style.opacity = '';
        startBtn.disabled = false;
        startBtn.onclick = () => window.location.href = '/homepage/';
    } else {
        startBtn.style.display = 'none';
    }
}

function checkExamStatus() {
    const currentUser = JSON.parse(localStorage.getItem('currentUser') || '{}');
    const userEmail = currentUser.email;
    
    if (!userEmail) return;
    
    // First check student status to see if exam is already submitted
    fetch('/assignments/student-status/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({ email: userEmail })
    })
    .then(response => response.json())
    .then(statusData => {
        const timerInfo = document.getElementById('timerInfo');
        
        // If assignment is completed, qualified, or rejected, hide the exam status message
        if (statusData.assignment_status === 'completed' || 
            statusData.assignment_status === 'qualified' || 
            statusData.assignment_status === 'rejected') {
            timerInfo.style.display = 'none';
            return;
        }
        
        // Otherwise, check exam status normally
        fetch('/assignments/exam-status/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ email: userEmail })
        })
        .then(response => response.json())
        .then(data => {
            if (data.is_active) {
                timerInfo.innerHTML = '<i class="fas fa-check-circle" style="color: #28a745;"></i><span>Exam is active - You can start!</span>';
            } else {
                timerInfo.innerHTML = '<i class="fas fa-clock" style="color: #ffc107;"></i><span>Exam not yet activated by admin. You can still start.</span>';
            }
        })
        .catch(error => {
            console.error('Error checking exam status:', error);
            timerInfo.innerHTML = '<i class="fas fa-exclamation-triangle" style="color: #ffc107;"></i><span>Error checking exam status. Please refresh.</span>';
        });
    })
    .catch(error => {
        console.error('Error checking student status:', error);
    });
}

// Get CSRF token function
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

function startAssignment() {
    // Check if assignment already completed
    const assignmentStatus = localStorage.getItem('assignmentStatus');
    if (assignmentStatus === 'completed') {
        alert('You have already completed the assignment.');
        return;
    }
    
    // Store that user started assignment
    localStorage.setItem('assignmentStarted', 'true');
    localStorage.setItem('assignmentStartTime', new Date().toISOString());
    
    // Redirect to first assignment page
    window.location.href = '/homepage/';
}

