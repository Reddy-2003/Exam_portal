// Registration form functionality
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('studentForm');
    const skillsDropdown = document.getElementById('skillsDropdown');
    const dropdownBtn = skillsDropdown.querySelector('.dropdown-btn');
    const dropdownList = skillsDropdown.querySelector('.dropdown-list');
    const skillsInput = document.getElementById('skills');

    // Skills dropdown functionality
    dropdownBtn.addEventListener('click', function() {
        dropdownList.classList.toggle('show');
    });

    // Close dropdown when clicking outside
    document.addEventListener('click', function(e) {
        if (!skillsDropdown.contains(e.target)) {
            dropdownList.classList.remove('show');
        }
    });

    // Handle skill selection
    const checkboxes = dropdownList.querySelectorAll('input[type="checkbox"]');
    checkboxes.forEach(checkbox => {
        checkbox.addEventListener('change', updateSelectedSkills);
    });

    function updateSelectedSkills() {
        const selected = [];
        checkboxes.forEach(checkbox => {
            if (checkbox.checked) {
                selected.push(checkbox.value);
            }
        });
        
        if (selected.length > 0) {
            dropdownBtn.textContent = selected.join(', ');
            dropdownBtn.style.color = '#2c3e50';
        } else {
            dropdownBtn.textContent = 'Select Skills';
            dropdownBtn.style.color = '#6c757d';
        }
        
        skillsInput.value = selected.join(',');
    }

    // Form submission
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        // Validate form
        if (!validateForm()) {
            return;
        }
        
        // Collect form data
        const formData = {
            name: document.getElementById('name').value,
            email: document.getElementById('email').value,
            mobile: document.getElementById('mobile').value,
            stream: document.getElementById('group').value,
            college: document.getElementById('college').value,
            skills: skillsInput.value,
            ssc_grade: document.getElementById('ssc').value,
            intermediate_grade: document.getElementById('inter').value
        };
        
        // Submit to server
        try {
            const response = await fetch('/api/register/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            });
            
            const result = await response.json();
            
            if (result.success) {
                alert(`Registration successful! Your login credentials:\nEmail: ${formData.email}\nPassword: ${result.password}\n\nPlease save these credentials and proceed to login.`);
                window.location.href = '/';
            } else {
                alert(result.message || 'Registration failed. Please try again.');
            }
        } catch (error) {
            alert('Registration failed. Please check your connection and try again.');
        }
    });

    // Form validation
    function validateForm() {
        const name = document.getElementById('name').value.trim();
        const email = document.getElementById('email').value.trim();
        const mobile = document.getElementById('mobile').value.trim();
        const stream = document.getElementById('group').value.trim();
        const college = document.getElementById('college').value.trim();
        const ssc = document.getElementById('ssc').value.trim();
        const inter = document.getElementById('inter').value.trim();
        
        if (!name) {
            alert('Please enter your name');
            return false;
        }
        
        if (!validateEmail(email)) {
            alert('Please enter a valid email address');
            return false;
        }
        
        if (!validateMobile(mobile)) {
            alert('Please enter a valid 10-digit mobile number');
            return false;
        }
        
        if (!stream) {
            alert('Please select your stream');
            return false;
        }
        
        if (!college) {
            alert('Please select your college');
            return false;
        }
        
        if (!ssc) {
            alert('Please enter your SSC grade');
            return false;
        }
        
        if (!inter) {
            alert('Please enter your Intermediate grade');
            return false;
        }
        
        return true;
    }

    // Email validation
    function validateEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }

    // Mobile validation
    function validateMobile(mobile) {
        const mobileRegex = /^[0-9]{10}$/;
        return mobileRegex.test(mobile);
    }
});