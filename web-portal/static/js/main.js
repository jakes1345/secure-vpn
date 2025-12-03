// PhazeVPN - Advanced Interactive JavaScript

(function() {
    'use strict';

    // ============================================
    // INITIALIZATION
    // ============================================
    
    document.addEventListener('DOMContentLoaded', function() {
        initScrollAnimations();
        initParticleBackground();
        initSmoothScrolling();
        initCardAnimations();
        initButtonRipple();
        initParallax();
        initCounterAnimations();
        initTypingEffect();
        initScrollProgress();
        initBackToTop();
        initMobileMenu();
    });

    // ============================================
    // SCROLL ANIMATIONS
    // ============================================
    
    function initScrollAnimations() {
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const observer = new IntersectionObserver(function(entries) {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('revealed');
                    observer.unobserve(entry.target);
                }
            });
        }, observerOptions);

        // Observe all cards and sections
        document.querySelectorAll('.card, .scroll-reveal, .animate-on-scroll').forEach(el => {
            el.classList.add('scroll-reveal');
            observer.observe(el);
        });
    }

    // ============================================
    // PARTICLE BACKGROUND
    // ============================================
    
    function initParticleBackground() {
        const particlesContainer = document.createElement('div');
        particlesContainer.className = 'particles-bg';
        document.body.appendChild(particlesContainer);

        const particleCount = 20;
        for (let i = 0; i < particleCount; i++) {
            const particle = document.createElement('div');
            particle.className = 'particle';
            particle.style.left = Math.random() * 100 + '%';
            particle.style.top = Math.random() * 100 + '%';
            particle.style.animationDelay = Math.random() * 6 + 's';
            particle.style.animationDuration = (Math.random() * 4 + 4) + 's';
            particlesContainer.appendChild(particle);
        }
    }

    // ============================================
    // SMOOTH SCROLLING
    // ============================================
    
    function initSmoothScrolling() {
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function(e) {
                const href = this.getAttribute('href');
                if (href !== '#' && href.length > 1) {
                    e.preventDefault();
                    const target = document.querySelector(href);
                    if (target) {
                        target.scrollIntoView({
                            behavior: 'smooth',
                            block: 'start'
                        });
                    }
                }
            });
        });
    }

    // ============================================
    // CARD ANIMATIONS
    // ============================================
    
    function initCardAnimations() {
        const cards = document.querySelectorAll('.card');
        
        cards.forEach((card, index) => {
            // Stagger animation
            card.style.animationDelay = (index * 0.1) + 's';
            card.classList.add('fade-in-up');
            
            // 3D tilt effect on hover
            card.addEventListener('mousemove', function(e) {
                const rect = card.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const y = e.clientY - rect.top;
                
                const centerX = rect.width / 2;
                const centerY = rect.height / 2;
                
                const rotateX = (y - centerY) / 10;
                const rotateY = (centerX - x) / 10;
                
                card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateY(-8px)`;
            });
            
            card.addEventListener('mouseleave', function() {
                card.style.transform = 'perspective(1000px) rotateX(0) rotateY(0) translateY(0)';
            });
        });
    }

    // ============================================
    // BUTTON RIPPLE EFFECT
    // ============================================
    
    function initButtonRipple() {
        document.querySelectorAll('.btn').forEach(button => {
            button.addEventListener('click', function(e) {
                const ripple = document.createElement('span');
                const rect = this.getBoundingClientRect();
                const size = Math.max(rect.width, rect.height);
                const x = e.clientX - rect.left - size / 2;
                const y = e.clientY - rect.top - size / 2;
                
                ripple.style.width = ripple.style.height = size + 'px';
                ripple.style.left = x + 'px';
                ripple.style.top = y + 'px';
                ripple.classList.add('ripple');
                
                this.appendChild(ripple);
                
                setTimeout(() => {
                    ripple.remove();
                }, 600);
            });
        });
    }

    // ============================================
    // PARALLAX EFFECT (Hero only, not cards)
    // ============================================
    
    function initParallax() {
        // Only apply parallax to hero, not cards (conflicts with 3D tilt)
        const hero = document.querySelector('.hero');
        
        if (hero) {
            window.addEventListener('scroll', PhazeVPN.throttle(function() {
                const scrolled = window.pageYOffset;
                const speed = 0.3;
                const yPos = -(scrolled * speed);
                hero.style.transform = `translateY(${yPos}px)`;
            }, 16));
        }
    }

    // ============================================
    // COUNTER ANIMATIONS
    // ============================================
    
    function initCounterAnimations() {
        const counters = document.querySelectorAll('[data-count]');
        
        const observer = new IntersectionObserver(function(entries) {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const counter = entry.target;
                    const target = parseInt(counter.getAttribute('data-count'));
                    const duration = 2000;
                    const increment = target / (duration / 16);
                    let current = 0;
                    
                    const updateCounter = () => {
                        current += increment;
                        if (current < target) {
                            counter.textContent = Math.floor(current);
                            requestAnimationFrame(updateCounter);
                        } else {
                            counter.textContent = target;
                        }
                    };
                    
                    updateCounter();
                    observer.unobserve(counter);
                }
            });
        });
        
        counters.forEach(counter => observer.observe(counter));
    }

    // ============================================
    // TYPING EFFECT
    // ============================================
    
    function initTypingEffect() {
        const typingElements = document.querySelectorAll('[data-typing]');
        
        typingElements.forEach(element => {
            const text = element.getAttribute('data-typing');
            const speed = parseInt(element.getAttribute('data-typing-speed')) || 100;
            let index = 0;
            
            element.textContent = '';
            
            const type = () => {
                if (index < text.length) {
                    element.textContent += text.charAt(index);
                    index++;
                    setTimeout(type, speed);
                }
            };
            
            // Start typing when element is visible
            const observer = new IntersectionObserver(function(entries) {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        type();
                        observer.unobserve(entry.target);
                    }
                });
            });
            
            observer.observe(element);
        });
    }

    // ============================================
    // NAVBAR SCROLL EFFECT
    // ============================================
    
    let lastScroll = 0;
    const navbar = document.querySelector('.navbar');
    
    window.addEventListener('scroll', function() {
        const currentScroll = window.pageYOffset;
        
        if (currentScroll > 100) {
            navbar.style.boxShadow = '0 4px 20px rgba(0, 0, 0, 0.3)';
            navbar.style.background = 'rgba(30, 41, 59, 0.98)';
        } else {
            navbar.style.boxShadow = 'none';
            navbar.style.background = 'rgba(30, 41, 59, 0.95)';
        }
        
        lastScroll = currentScroll;
    });

    // ============================================
    // CURSOR TRAIL EFFECT (Optional)
    // ============================================
    
    function initCursorTrail() {
        const trail = [];
        const trailLength = 10;
        
        for (let i = 0; i < trailLength; i++) {
            const dot = document.createElement('div');
            dot.className = 'cursor-trail';
            dot.style.cssText = `
                position: fixed;
                width: 4px;
                height: 4px;
                background: var(--primary);
                border-radius: 50%;
                pointer-events: none;
                z-index: 9999;
                opacity: ${1 - (i / trailLength)};
                transform: translate(-50%, -50%);
                transition: all 0.1s ease;
            `;
            document.body.appendChild(dot);
            trail.push({ element: dot, x: 0, y: 0 });
        }
        
        document.addEventListener('mousemove', function(e) {
            trail.forEach((dot, index) => {
                setTimeout(() => {
                    dot.x = e.clientX;
                    dot.y = e.clientY;
                    dot.element.style.left = dot.x + 'px';
                    dot.element.style.top = dot.y + 'px';
                }, index * 20);
            });
        });
    }

    // Uncomment to enable cursor trail
    // initCursorTrail();

    // ============================================
    // LOADING ANIMATION
    // ============================================
    
    window.addEventListener('load', function() {
        document.body.classList.add('loaded');
        
        // Fade in page content
        const mainContent = document.querySelector('main');
        if (mainContent) {
            mainContent.style.opacity = '0';
            mainContent.style.transition = 'opacity 0.5s ease';
            
            setTimeout(() => {
                mainContent.style.opacity = '1';
            }, 100);
        }
    });

    // ============================================
    // FORM VALIDATION ANIMATIONS
    // ============================================
    
    document.querySelectorAll('input, textarea, select').forEach(input => {
        input.addEventListener('focus', function() {
            this.parentElement.classList.add('focused');
        });
        
        input.addEventListener('blur', function() {
            if (!this.value) {
                this.parentElement.classList.remove('focused');
            }
        });
        
        input.addEventListener('invalid', function() {
            this.classList.add('shake');
            setTimeout(() => {
                this.classList.remove('shake');
            }, 500);
        });
    });

    // ============================================
    // UTILITY FUNCTIONS
    // ============================================
    
    // Debounce function
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    // Throttle function
    function throttle(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }

    // ============================================
    // SCROLL PROGRESS BAR
    // ============================================
    
    function initScrollProgress() {
        const progressBar = document.createElement('div');
        progressBar.className = 'scroll-progress';
        progressBar.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 0%;
            height: 3px;
            background: linear-gradient(90deg, var(--primary), var(--secondary));
            z-index: 10000;
            transition: width 0.1s ease;
            box-shadow: 0 2px 10px rgba(99, 102, 241, 0.5);
        `;
        document.body.appendChild(progressBar);
        
        window.addEventListener('scroll', PhazeVPN.throttle(function() {
            const windowHeight = document.documentElement.scrollHeight - document.documentElement.clientHeight;
            const scrolled = (window.pageYOffset / windowHeight) * 100;
            progressBar.style.width = scrolled + '%';
        }, 16));
    }

    // ============================================
    // BACK TO TOP BUTTON
    // ============================================
    
    function initBackToTop() {
        const backToTop = document.createElement('button');
        backToTop.className = 'back-to-top';
        backToTop.innerHTML = '↑';
        backToTop.style.cssText = `
            position: fixed;
            bottom: 30px;
            right: 30px;
            width: 50px;
            height: 50px;
            border-radius: 50%;
            background: var(--primary);
            color: white;
            border: none;
            font-size: 24px;
            cursor: pointer;
            opacity: 0;
            visibility: hidden;
            transition: all 0.3s ease;
            z-index: 1000;
            box-shadow: 0 4px 15px rgba(99, 102, 241, 0.4);
        `;
        document.body.appendChild(backToTop);
        
        backToTop.addEventListener('click', function() {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
        
        window.addEventListener('scroll', PhazeVPN.throttle(function() {
            if (window.pageYOffset > 300) {
                backToTop.style.opacity = '1';
                backToTop.style.visibility = 'visible';
                backToTop.style.transform = 'translateY(0)';
            } else {
                backToTop.style.opacity = '0';
                backToTop.style.visibility = 'hidden';
                backToTop.style.transform = 'translateY(20px)';
            }
        }, 100));
        
        backToTop.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-5px) scale(1.1)';
            this.style.boxShadow = '0 6px 20px rgba(99, 102, 241, 0.6)';
        });
        
        backToTop.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0) scale(1)';
            this.style.boxShadow = '0 4px 15px rgba(99, 102, 241, 0.4)';
        });
    }

    // ============================================
    // MOBILE MENU
    // ============================================
    
    function initMobileMenu() {
        const navbar = document.querySelector('.navbar-nav');
        if (!navbar) return;
        
        // Create hamburger button
        const hamburger = document.createElement('button');
        hamburger.className = 'mobile-menu-toggle';
        hamburger.innerHTML = '☰';
        hamburger.style.cssText = `
            display: none;
            background: transparent;
            border: none;
            color: var(--text-primary);
            font-size: 24px;
            cursor: pointer;
            padding: 8px;
        `;
        
        const navbarContainer = document.querySelector('.navbar-container');
        if (navbarContainer) {
            navbarContainer.insertBefore(hamburger, navbar);
        }
        
        // Toggle menu
        hamburger.addEventListener('click', function() {
            navbar.classList.toggle('mobile-open');
            hamburger.innerHTML = navbar.classList.contains('mobile-open') ? '✕' : '☰';
        });
        
        // Close on window resize
        window.addEventListener('resize', function() {
            if (window.innerWidth > 768) {
                navbar.classList.remove('mobile-open');
                hamburger.innerHTML = '☰';
            }
        });
        
        // Media query for mobile
        if (window.innerWidth <= 768) {
            hamburger.style.display = 'block';
            navbar.style.cssText += `
                position: fixed;
                top: 60px;
                left: 0;
                width: 100%;
                background: var(--bg-secondary);
                flex-direction: column;
                padding: 1rem;
                transform: translateX(-100%);
                transition: transform 0.3s ease;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
            `;
            
            navbar.classList.add('mobile-menu');
            
            const style = document.createElement('style');
            style.textContent = `
                .mobile-menu.mobile-open {
                    transform: translateX(0) !important;
                }
                @media (min-width: 769px) {
                    .mobile-menu-toggle { display: none !important; }
                    .mobile-menu { transform: none !important; position: static !important; }
                }
            `;
            document.head.appendChild(style);
        }
    }

    // Export for use in other scripts
    window.PhazeVPN = {
        debounce: debounce,
        throttle: throttle
    };

})();
