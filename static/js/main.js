/**
 * MegicAI - Main JavaScript
 * Common functionality used across the application
 */

// Helper function to format numbers with commas
function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

// Update credit display with animation
function updateCredits(newValue, animate = true) {
    const creditDisplay = document.querySelector('.credit-value');
    if (!creditDisplay) return;
    
    const currentValue = parseInt(creditDisplay.textContent.replace(/,/g, ''), 10);
    
    if (animate && !isNaN(currentValue)) {
        const diff = newValue - currentValue;
        const duration = 1000; // 1 second animation
        const startTime = performance.now();
        
        function updateCounter(timestamp) {
            const elapsed = timestamp - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const currentCount = Math.floor(currentValue + (diff * progress));
            
            creditDisplay.textContent = formatNumber(currentCount);
            
            if (progress < 1) {
                requestAnimationFrame(updateCounter);
            } else {
                creditDisplay.textContent = formatNumber(newValue);
            }
        }
        
        requestAnimationFrame(updateCounter);
    } else {
        creditDisplay.textContent = formatNumber(newValue);
    }
}

// Copy text to clipboard
function copyToClipboard(text, successCallback = null) {
    navigator.clipboard.writeText(text)
        .then(() => {
            if (successCallback) successCallback();
        })
        .catch(err => {
            console.error('Failed to copy text: ', err);
        });
}

// Toggle visibility of an element
function toggleVisibility(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.style.display = element.style.display === 'none' ? 'block' : 'none';
    }
}

// Add suggestions to a textarea
function addSuggestionToPrompt(suggestion, elementId) {
    const textarea = document.getElementById(elementId);
    if (textarea) {
        const currentText = textarea.value;
        textarea.value = currentText ? `${currentText}\n${suggestion}` : suggestion;
        textarea.focus();
    }
}

// Form validation
function validateForm(formId, errorElementId = null) {
    const form = document.getElementById(formId);
    if (!form) return true;
    
    let isValid = true;
    const requiredInputs = form.querySelectorAll('[required]');
    
    // Clear previous error messages
    form.querySelectorAll('.field-error').forEach(el => el.remove());
    
    requiredInputs.forEach(input => {
        if (!input.value.trim()) {
            isValid = false;
            
            // Create error message
            const errorMsg = document.createElement('div');
            errorMsg.className = 'field-error';
            errorMsg.textContent = 'This field is required';
            input.parentNode.appendChild(errorMsg);
            
            // Add error style to input
            input.classList.add('input-error');
        } else {
            input.classList.remove('input-error');
        }
    });
    
    // If there's a global error element, update it
    if (!isValid && errorElementId) {
        const errorElement = document.getElementById(errorElementId);
        if (errorElement) {
            errorElement.textContent = 'Please fill in all required fields';
            errorElement.style.display = 'block';
        }
    }
    
    return isValid;
}

// Handle form submission with AJAX
function submitFormAsync(formId, successCallback, errorCallback) {
    const form = document.getElementById(formId);
    if (!form) return;
    
    form.addEventListener('submit', function(event) {
        event.preventDefault();
        
        if (!validateForm(formId)) return;
        
        const formData = new FormData(form);
        const submitButton = form.querySelector('button[type="submit"]');
        
        if (submitButton) {
            const originalText = submitButton.innerHTML;
            submitButton.disabled = true;
            submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
        }
        
        fetch(form.action, {
            method: form.method,
            body: formData
        })
        .then(response => {
            // Check if the response is JSON or HTML
            const contentType = response.headers.get('content-type');
            if (!response.ok) {
                if (contentType && contentType.includes('application/json')) {
                    return response.json().then(data => {
                        throw new Error(data.message || 'An error occurred');
                    });
                } else {
                    // For non-JSON errors, just show the status text instead of trying to parse JSON
                    throw new Error('Server error occurred: ' + response.statusText);
                }
            }
            
            // If response is HTML, handle it as a redirect
            if (contentType && contentType.includes('text/html')) {
                // This is an HTML response, likely a result page - redirect to it
                window.location.href = response.url;
                return { success: true, redirected: true };
            }
            
            // Check if it's a redirect (e.g., 302, 303)
            if (response.redirected) {
                window.location.href = response.url;
                return { success: true, redirected: true };
            }
            
            // Otherwise process as JSON
            if (contentType && contentType.includes('application/json')) {
                return response.json();
            } else {
                // If it's not JSON and not HTML with a redirect, handle it as a success
                return { success: true, message: "Operation completed successfully" };
            }
        })
        .then(data => {
            if (successCallback) successCallback(data);
        })
        .catch(error => {
            console.error("Error during form submission:", error);
            if (errorCallback) errorCallback(error.message);
        })
        .finally(() => {
            if (submitButton) {
                submitButton.disabled = false;
                submitButton.innerHTML = originalText;
            }
        });
    });
}

// Document ready event
document.addEventListener('DOMContentLoaded', function() {
    console.log('MegicAI application initialized');
    
    // Initialize any forms with async submission
    const asyncForms = document.querySelectorAll('[data-async-submit]');
    asyncForms.forEach(form => {
        const formId = form.id;
        const successTarget = form.getAttribute('data-success-target');
        const errorTarget = form.getAttribute('data-error-target');
        
        // Check if the form is for HTML-based operations like process-request
        const actionUrl = form.getAttribute('action');
        if (actionUrl && (actionUrl.includes('/process-request') || actionUrl.includes('/watch-ad'))) {
            // These endpoints return HTML, not JSON - use regular form submission
            console.log('Form will use direct submission:', actionUrl);
            form.removeAttribute('data-async-submit');
            
            // Add regular submit handler with validation
            form.addEventListener('submit', function(event) {
                if (!validateForm(formId)) {
                    event.preventDefault();
                    return false;
                }
                
                const submitButton = form.querySelector('button[type="submit"]');
                if (submitButton) {
                    // Add loading indicator
                    const originalText = submitButton.innerHTML;
                    submitButton.disabled = true;
                    submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
                    
                    // Make sure the form submits normally for HTML responses
                    setTimeout(() => {
                        if (submitButton.disabled) {
                            // Re-enable after a timeout just in case
                            submitButton.disabled = false;
                            submitButton.innerHTML = originalText;
                        }
                    }, 10000); // 10 second timeout
                }
                
                return true;
            });
        } else {
            // Use async submission for JSON-based API endpoints
            submitFormAsync(
                formId,
                data => {
                    if (successTarget) {
                        const targetElement = document.getElementById(successTarget);
                        if (targetElement) {
                            targetElement.textContent = data.message || 'Success!';
                            targetElement.style.display = 'block';
                        }
                    }
                    
                    // If a redirect URL is provided in the response
                    if (data.redirect) {
                        window.location.href = data.redirect;
                    }
                },
                error => {
                    if (errorTarget) {
                        const targetElement = document.getElementById(errorTarget);
                        if (targetElement) {
                            targetElement.textContent = error;
                            targetElement.style.display = 'block';
                        }
                    }
                }
            );
        }
    });
}); 