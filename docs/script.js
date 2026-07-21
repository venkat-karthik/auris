/* ============================================
   AURIS DOCUMENTATION - INTERACTIVE SCRIPT
   ============================================ */

document.addEventListener('DOMContentLoaded', function() {
    initializeNavigation();
    initializeWorkflows();
    initializeScrollAnimations();
    initializeIntersectionObserver();
});

/* ============================================
   NAVIGATION FUNCTIONALITY
   ============================================ */

function initializeNavigation() {
    const navLinks = document.querySelectorAll('.nav-link');
    const hamburger = document.querySelector('.hamburger');
    const navMenu = document.querySelector('.nav-menu');

    // Smooth scroll and active link tracking
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Update active state
            navLinks.forEach(l => l.classList.remove('active'));
            this.classList.add('active');

            // Get section and scroll
            const section = this.getAttribute('data-section');
            scrollToSection(section);
        });
    });

    // Hamburger menu toggle (mobile)
    if (hamburger) {
        hamburger.addEventListener('click', function() {
            navMenu.style.display = navMenu.style.display === 'flex' ? 'none' : 'flex';
        });
    }

    // Update active nav on scroll
    window.addEventListener('scroll', updateActiveNav);
}

function updateActiveNav() {
    const navLinks = document.querySelectorAll('.nav-link');
    let current = '';

    const sections = document.querySelectorAll('section');
    sections.forEach(section => {
        const sectionTop = section.offsetTop;
        const sectionHeight = section.clientHeight;
        if (pageYOffset >= (sectionTop - 200)) {
            current = section.getAttribute('id');
        }
    });

    navLinks.forEach(link => {
        link.classList.remove('active');
        if (link.getAttribute('data-section') === current) {
            link.classList.add('active');
        }
    });
}

function scrollToSection(sectionId) {
    const section = document.getElementById(sectionId);
    if (section) {
        section.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
}

/* ============================================
   WORKFLOW FUNCTIONALITY
   ============================================ */

function initializeWorkflows() {
    const tabs = document.querySelectorAll('.workflow-tab');

    tabs.forEach(tab => {
        tab.addEventListener('click', function() {
            const workflowNumber = this.textContent.match(/\d+/)[0];
            openWorkflow(workflowNumber);
        });
    });
}

function openWorkflow(workflowNumber) {
    // Hide all workflows
    const workflows = document.querySelectorAll('.workflow-content');
    workflows.forEach(w => w.classList.remove('active'));

    // Show selected workflow
    const selectedWorkflow = document.getElementById(`workflow-${workflowNumber}`);
    if (selectedWorkflow) {
        selectedWorkflow.classList.add('active');
        selectedWorkflow.style.animation = 'fadeIn 0.3s ease-out';
    }

    // Update active tab
    const tabs = document.querySelectorAll('.workflow-tab');
    tabs.forEach(tab => tab.classList.remove('active'));
    tabs[workflowNumber - 1].classList.add('active');
}

/* ============================================
   SCROLL ANIMATIONS
   ============================================ */

function initializeScrollAnimations() {
    const animatedElements = document.querySelectorAll(
        '.fade-in, .fade-in-up, .fade-in-down, .fade-in-left, .fade-in-right, ' +
        '.slide-in-left, .slide-in-right, .slide-in-up, .scale-in'
    );

    animatedElements.forEach((element, index) => {
        element.style.opacity = '0';
        element.style.animation = 'none';
        
        // Add delay for staggered effect
        if (element.classList.contains('fade-in-up')) {
            element.style.animationDelay = (index * 0.1) + 's';
        }
    });
}

function initializeIntersectionObserver() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -100px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                // Trigger animation classes
                if (entry.target.classList.contains('fade-in')) {
                    entry.target.style.animation = 'fadeIn 0.8s ease-out forwards';
                } else if (entry.target.classList.contains('fade-in-up')) {
                    entry.target.style.animation = 'fadeInUp 0.8s ease-out forwards';
                } else if (entry.target.classList.contains('fade-in-down')) {
                    entry.target.style.animation = 'fadeInDown 0.8s ease-out forwards';
                } else if (entry.target.classList.contains('fade-in-left')) {
                    entry.target.style.animation = 'fadeInLeft 0.8s ease-out forwards';
                } else if (entry.target.classList.contains('fade-in-right')) {
                    entry.target.style.animation = 'fadeInRight 0.8s ease-out forwards';
                } else if (entry.target.classList.contains('slide-in-left')) {
                    entry.target.style.animation = 'slideInLeft 0.8s ease-out forwards';
                } else if (entry.target.classList.contains('slide-in-right')) {
                    entry.target.style.animation = 'slideInRight 0.8s ease-out forwards';
                } else if (entry.target.classList.contains('slide-in-up')) {
                    entry.target.style.animation = 'slideInUp 0.8s ease-out forwards';
                } else if (entry.target.classList.contains('scale-in')) {
                    entry.target.style.animation = 'scaleIn 0.6s ease-out forwards';
                }

                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    const animatedElements = document.querySelectorAll(
        '.fade-in, .fade-in-up, .fade-in-down, .fade-in-left, .fade-in-right, ' +
        '.slide-in-left, .slide-in-right, .slide-in-up, .scale-in'
    );

    animatedElements.forEach(element => {
        observer.observe(element);
    });
}

/* ============================================
   CODE COPY FUNCTIONALITY
   ============================================ */

function initializeCodeCopy() {
    const codeBlocks = document.querySelectorAll('.code-block');

    codeBlocks.forEach(block => {
        // Add copy button
        const copyBtn = document.createElement('button');
        copyBtn.textContent = 'Copy';
        copyBtn.className = 'code-copy-btn';
        copyBtn.style.cssText = `
            position: absolute;
            top: 10px;
            right: 10px;
            background: var(--primary-color);
            color: white;
            border: none;
            padding: 5px 10px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.8rem;
            opacity: 0;
            transition: opacity 0.3s ease;
        `;

        block.style.position = 'relative';
        block.appendChild(copyBtn);

        // Show/hide copy button
        block.addEventListener('mouseenter', () => copyBtn.style.opacity = '1');
        block.addEventListener('mouseleave', () => copyBtn.style.opacity = '0');

        // Copy functionality
        copyBtn.addEventListener('click', () => {
            const text = block.querySelector('pre').textContent;
            navigator.clipboard.writeText(text).then(() => {
                copyBtn.textContent = 'Copied!';
                setTimeout(() => {
                    copyBtn.textContent = 'Copy';
                }, 2000);
            });
        });
    });
}

/* ============================================
   PERFORMANCE METRICS DISPLAY
   ============================================ */

function displayPerformanceMetrics() {
    const metrics = {
        'Page Load Time': window.performance.timing.loadEventEnd - window.performance.timing.navigationStart + 'ms',
        'DOM Content Loaded': window.performance.timing.domContentLoadedEventEnd - window.performance.timing.navigationStart + 'ms',
        'First Paint': performance.getEntriesByName('first-paint')[0]?.startTime.toFixed(2) + 'ms' || 'N/A'
    };

    console.log('Performance Metrics:', metrics);
}

/* ============================================
   TRACKING & ANALYTICS
   ============================================ */

function trackUserInteraction(action, details) {
    if (typeof gtag !== 'undefined') {
        gtag('event', action, details);
    }
    console.log(`User Action: ${action}`, details);
}

// Track section views
document.addEventListener('scroll', function() {
    const sections = document.querySelectorAll('section');
    sections.forEach(section => {
        const rect = section.getBoundingClientRect();
        if (rect.top < window.innerHeight / 2 && rect.bottom > window.innerHeight / 2) {
            trackUserInteraction('section_view', {
                section_name: section.getAttribute('id')
            });
        }
    });
});

/* ============================================
   UTILITY FUNCTIONS
   ============================================ */

function addClassWithDelay(element, className, delay) {
    setTimeout(() => {
        element.classList.add(className);
    }, delay);
}

function removeClassWithDelay(element, className, delay) {
    setTimeout(() => {
        element.classList.remove(className);
    }, delay);
}

function toggleAnimation(element, animationClass, duration = 500) {
    element.classList.add(animationClass);
    setTimeout(() => {
        element.classList.remove(animationClass);
    }, duration);
}

/* ============================================
   THEME SWITCHER (OPTIONAL)
   ============================================ */

function initializeThemeSwitcher() {
    const html = document.documentElement;
    const savedTheme = localStorage.getItem('theme') || 'dark';
    
    html.setAttribute('data-theme', savedTheme);

    if (typeof themeSwitcher !== 'undefined') {
        themeSwitcher.addEventListener('change', function() {
            const theme = this.checked ? 'light' : 'dark';
            html.setAttribute('data-theme', theme);
            localStorage.setItem('theme', theme);
        });
    }
}

/* ============================================
   SMOOTH SCROLL BEHAVIOR
   ============================================ */

function enableSmoothScroll() {
    document.documentElement.style.scrollBehavior = 'smooth';
}

/* ============================================
   LAZY LOAD IMAGES (OPTIONAL)
   ============================================ */

function initializeLazyLoad() {
    const images = document.querySelectorAll('img[data-src]');
    
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.src = entry.target.dataset.src;
                entry.target.classList.add('loaded');
                observer.unobserve(entry.target);
            }
        });
    });

    images.forEach(img => imageObserver.observe(img));
}

/* ============================================
   INITIALIZE ALL
   ============================================ */

function initializeAll() {
    enableSmoothScroll();
    initializeCodeCopy();
    displayPerformanceMetrics();
    initializeThemeSwitcher();
    initializeLazyLoad();
}

// Run initialization when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeAll);
} else {
    initializeAll();
}

/* ============================================
   EXPORT FUNCTIONS FOR GLOBAL USE
   ============================================ */

window.scrollToSection = scrollToSection;
window.openWorkflow = openWorkflow;
window.toggleAnimation = toggleAnimation;
