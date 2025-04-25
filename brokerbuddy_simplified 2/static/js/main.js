// BrokerBuddy Simplified - Main JavaScript
// Provides interactive functionality for the BrokerBuddy application

document.addEventListener('DOMContentLoaded', function() {
    // Initialize date in footer
    updateFooterYear();
    
    // Initialize form validation
    initFormValidation();
    
    // Initialize responsive navigation
    initResponsiveNav();
    
    // Initialize print functionality
    initPrintButton();
});

// Update footer year to current year
function updateFooterYear() {
    const yearElements = document.querySelectorAll('.footer-bottom');
    const currentYear = new Date().getFullYear();
    
    yearElements.forEach(element => {
        const content = element.innerHTML;
        element.innerHTML = content.replace('{{ now.year }}', currentYear);
    });
}

// Form validation for client information form
function initFormValidation() {
    const clientForm = document.querySelector('form[action*="submit-client"]');
    
    if (clientForm) {
        clientForm.addEventListener('submit', function(event) {
            const requiredFields = clientForm.querySelectorAll('[required]');
            let isValid = true;
            
            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    isValid = false;
                    field.classList.add('is-invalid');
                } else {
                    field.classList.remove('is-invalid');
                }
            });
            
            // Validate numeric fields
            const numericFields = ['monthly_revenue', 'equipment_cost'];
            
            numericFields.forEach(fieldName => {
                const field = clientForm.querySelector(`[name="${fieldName}"]`);
                
                if (field && field.value.trim()) {
                    const value = field.value.trim();
                    
                    if (isNaN(parseFloat(value)) || !isFinite(value) || parseFloat(value) <= 0) {
                        isValid = false;
                        field.classList.add('is-invalid');
                    } else {
                        field.classList.remove('is-invalid');
                    }
                }
            });
            
            if (!isValid) {
                event.preventDefault();
                alert('Please fill in all required fields correctly.');
            }
        });
    }
}

// Responsive navigation for mobile devices
function initResponsiveNav() {
    const navMenu = document.querySelector('.nav-menu');
    
    if (window.innerWidth <= 768 && navMenu) {
        const menuToggle = document.createElement('button');
        menuToggle.className = 'menu-toggle';
        menuToggle.innerHTML = '☰';
        
        const headerContainer = document.querySelector('.header-container');
        headerContainer.insertBefore(menuToggle, navMenu);
        
        menuToggle.addEventListener('click', function() {
            navMenu.classList.toggle('active');
        });
    }
}

// Initialize print functionality for results page
function initPrintButton() {
    const printButton = document.getElementById('print-results');
    
    if (printButton) {
        printButton.addEventListener('click', function() {
            window.print();
        });
    }
}

// Format currency values
function formatCurrency(value) {
    if (!value) return '$0.00';
    
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(value);
}

// Smooth scrolling for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
        e.preventDefault();
        
        const targetId = this.getAttribute('href');
        
        if (targetId === '#') return;
        
        const targetElement = document.querySelector(targetId);
        
        if (targetElement) {
            window.scrollTo({
                top: targetElement.offsetTop - 100,
                behavior: 'smooth'
            });
        }
    });
});
