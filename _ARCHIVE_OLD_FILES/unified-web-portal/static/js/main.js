// Main JavaScript for Unified Platform

// Initialize app
document.addEventListener('DOMContentLoaded', function() {
    console.log('PhazeVPN Unified Platform loaded');
    
    // Add smooth transitions
    document.querySelectorAll('a').forEach(link => {
        link.addEventListener('click', function(e) {
            if (this.href && !this.href.includes('#')) {
                // Smooth page transitions
            }
        });
    });
    
    // Email interface interactions
    if (document.getElementById('emailList')) {
        initEmailInterface();
    }
});

function initEmailInterface() {
    const emailItems = document.querySelectorAll('.email-item');
    const emailView = document.getElementById('emailView');
    
    emailItems.forEach(item => {
        item.addEventListener('click', function() {
            // Remove active class from all items
            emailItems.forEach(i => i.classList.remove('active'));
            // Add active class to clicked item
            this.classList.add('active');
            
            // Load email content
            loadEmailContent(this);
        });
    });
}

function loadEmailContent(emailItem) {
    const emailView = document.getElementById('emailView');
    const sender = emailItem.querySelector('.email-sender').textContent;
    const subject = emailItem.querySelector('.email-subject').textContent;
    
    emailView.innerHTML = `
        <div class="email-view-content">
            <div class="email-view-header">
                <h2>${subject}</h2>
                <div class="email-meta">
                    <div class="email-from">
                        <strong>From:</strong> ${sender}
                    </div>
                    <div class="email-date">
                        <strong>Date:</strong> ${new Date().toLocaleString()}
                    </div>
                </div>
            </div>
            <div class="email-body">
                <p>Email content will be loaded here...</p>
            </div>
        </div>
    `;
}

// API helper functions
async function apiCall(endpoint, method = 'GET', data = null) {
    try {
        const options = {
            method,
            headers: {
                'Content-Type': 'application/json',
            }
        };
        
        if (data) {
            options.body = JSON.stringify(data);
        }
        
        const response = await fetch(endpoint, options);
        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        return null;
    }
}
