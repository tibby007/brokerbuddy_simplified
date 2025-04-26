// BrokerBuddy Main JavaScript File

document.addEventListener('DOMContentLoaded', function() {
    // Mobile Menu Functionality
    setupMobileMenu();
    
    // Animation Effects
    setupAnimations();
    
    // Form Validation (if on client form page)
    if (document.querySelector('form')) {
        setupFormValidation();
    }
});

// Mobile Menu Setup
function setupMobileMenu() {
    const headerContainer = document.querySelector('.header-container');
    const nav = document.querySelector('.nav-menu');
    
    // Only setup mobile menu if we're on a mobile device
    if (window.innerWidth <= 768 && headerContainer && nav) {
        // Create menu toggle button
        const menuToggle = document.createElement('button');
        menuToggle.className = 'menu-toggle';
        menuToggle.innerHTML = '<span></span><span></span><span></span>';
        headerContainer.appendChild(menuToggle);
        
        // Create overlay
        const overlay = document.createElement('div');
        overlay.className = 'menu-overlay';
        document.body.appendChild(overlay);
        
        // Toggle menu
        menuToggle.addEventListener('click', function() {
            menuToggle.classList.toggle('active');
            nav.classList.toggle('active');
            overlay.classList.toggle('active');
            document.body.classList.toggle('menu-open');
        });
        
        // Close menu when clicking overlay
        overlay.addEventListener('click', function() {
            menuToggle.classList.remove('active');
            nav.classList.remove('active');
            overlay.classList.remove('active');
            document.body.classList.remove('menu-open');
        });
        
        // Close menu when clicking a link
        nav.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', function() {
                menuToggle.classList.remove('active');
                nav.classList.remove('active');
                overlay.classList.remove('active');
                document.body.classList.remove('menu-open');
            });
        });
    }
}

// Animation Setup
function setupAnimations() {
    // Add float animation to hero image
    const heroImage = document.querySelector('.hero-image');
    if (heroImage) {
        heroImage.classList.add('float');
    }
    
    // Add gradient text effect to selected headings
    const heroHeading = document.querySelector('.hero-content h1');
    if (heroHeading) {
        const text = heroHeading.innerHTML;
        const enhancedText = text.replace('AI-Powered', '<span class="gradient-text">AI-Powered</span>');
        heroHeading.innerHTML = enhancedText;
    }
    
    // Add 3D card effect to feature cards
    const featureCards = document.querySelectorAll('.feature-card');
    featureCards.forEach(card => {
        card.classList.add('card-3d');
    });
    
    // Add pulse animation to CTA button
    const ctaButton = document.querySelector('.cta .btn');
    if (ctaButton) {
        ctaButton.classList.add('pulse');
    }
    
    // Add data-number attributes to feature headings
    const featureHeadings = document.querySelectorAll('.feature-card h3');
    featureHeadings.forEach(heading => {
        // Extract number from heading text if it starts with a number
        const match = heading.textContent.match(/^(\d+)\./);
        if (match && match[1]) {
            heading.setAttribute('data-number', match[1]);
        }
    });
    
    // Add background shapes to sections
    addBackgroundShapes();
    
    // Setup intersection observer for scroll animations
    setupScrollAnimations();
}

// Add background shapes to sections
function addBackgroundShapes() {
    const sections = ['.benefits', '.about', '.working-capital'];
    
    sections.forEach((sectionClass, index) => {
        const section = document.querySelector(sectionClass);
        if (section) {
            const shape1 = document.createElement('div');
            shape1.className = 'bg-shape bg-shape-1';
            
            const shape2 = document.createElement('div');
            shape2.className = 'bg-shape bg-shape-2';
            
            section.appendChild(shape1);
            section.appendChild(shape2);
        }
    });
}

// Setup scroll animations using Intersection Observer
function setupScrollAnimations() {
    // Check if IntersectionObserver is supported
    if ('IntersectionObserver' in window) {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('show');
                }
            });
        }, { threshold: 0.1 });
        
        // Observe feature cards and benefit cards
        document.querySelectorAll('.feature-card, .benefit-card').forEach(card => {
            observer.observe(card);
        });
    } else {
        // Fallback for browsers that don't support IntersectionObserver
        document.querySelectorAll('.feature-card, .benefit-card').forEach(card => {
            card.classList.add('show');
        });
    }
}

// Form Validation
function setupFormValidation() {
    const form = document.querySelector('form');
    
    if (form) {
        form.addEventListener('submit', function(event) {
            let isValid = true;
            
            // Get all required inputs
            const requiredInputs = form.querySelectorAll('[required]');
            
            requiredInputs.forEach(input => {
                if (!input.value.trim()) {
                    isValid = false;
                    input.classList.add('error');
                    
                    // Create error message if it doesn't exist
                    let errorMsg = input.parentNode.querySelector('.error-message');
                    if (!errorMsg) {
                        errorMsg = document.createElement('div');
                        errorMsg.className = 'error-message';
                        errorMsg.textContent = 'This field is required';
                        input.parentNode.appendChild(errorMsg);
                    }
                } else {
                    input.classList.remove('error');
                    const errorMsg = input.parentNode.querySelector('.error-message');
                    if (errorMsg) {
                        errorMsg.remove();
                    }
                }
            });
            
            if (!isValid) {
                event.preventDefault();
            }
        });
        
        // Remove error styling when user starts typing
        form.querySelectorAll('input, select, textarea').forEach(input => {
            input.addEventListener('input', function() {
                this.classList.remove('error');
                const errorMsg = this.parentNode.querySelector('.error-message');
                if (errorMsg) {
                    errorMsg.remove();
                }
            });
        });
    }
}
