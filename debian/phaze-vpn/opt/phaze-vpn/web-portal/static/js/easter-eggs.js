// PhazeVPN - Easter Egg System
// Find all easter eggs to get 1 month free premium!

(function() {
    'use strict';

    const EASTER_EGGS = {
        'logo-click': {
            name: 'Logo Lover',
            description: 'Click the logo 3 times',
            found: false,
            hint: 'Click the logo a few times...'
        },
        'scroll-to-bottom': {
            name: 'Bottom Explorer',
            description: 'Scroll to the bottom of the page',
            found: false,
            hint: 'Scroll all the way down...'
        },
        'click-hero-button': {
            name: 'Button Clicker',
            description: 'Click any "Get Started" button',
            found: false,
            hint: 'Click a Get Started button...'
        },
        'hover-feature-card': {
            name: 'Card Hover',
            description: 'Hover over any feature card',
            found: false,
            hint: 'Hover over a feature card...'
        },
        'visit-pricing': {
            name: 'Price Checker',
            description: 'Visit the pricing page',
            found: false,
            hint: 'Check out our pricing...'
        },
        'visit-download': {
            name: 'Download Explorer',
            description: 'Visit the download page',
            found: false,
            hint: 'Check the download page...'
        },
        'click-signup': {
            name: 'Sign Up Click',
            description: 'Click the Sign Up button',
            found: false,
            hint: 'Try signing up...'
        },
        'hover-logo': {
            name: 'Logo Hover',
            description: 'Hover over the logo',
            found: false,
            hint: 'Hover over the logo...'
        },
        'scroll-halfway': {
            name: 'Mid Scroller',
            description: 'Scroll halfway down the page',
            found: false,
            hint: 'Scroll to the middle...'
        },
        'click-cta': {
            name: 'CTA Clicker',
            description: 'Click any call-to-action button',
            found: false,
            hint: 'Click a CTA button...'
        }
    };

    let foundCount = 0;
    let logoClickCount = 0;
    let scrolledHalfway = false;
    let scrolledToBottom = false;

    // Load found eggs from localStorage
    function loadFoundEggs() {
        const saved = localStorage.getItem('phazevpn_easter_eggs');
        if (saved) {
            const found = JSON.parse(saved);
            found.forEach(id => {
                if (EASTER_EGGS[id]) {
                    EASTER_EGGS[id].found = true;
                    foundCount++;
                }
            });
        }
        updateCounter();
    }

    // Save found egg
    function saveFoundEgg(id) {
        if (EASTER_EGGS[id] && !EASTER_EGGS[id].found) {
            EASTER_EGGS[id].found = true;
            foundCount++;
            
            const saved = localStorage.getItem('phazevpn_easter_eggs');
            const found = saved ? JSON.parse(saved) : [];
            if (!found.includes(id)) {
                found.push(id);
                localStorage.setItem('phazevpn_easter_eggs', JSON.stringify(found));
            }
            
            showEasterEggNotification(id);
            updateCounter();
            checkAllFound();
        }
    }

    // Show notification
    function showEasterEggNotification(id) {
        const egg = EASTER_EGGS[id];
        
        // Create notification
        const notification = document.createElement('div');
        notification.className = 'easter-egg-notification';
        notification.innerHTML = `
            <div class="easter-egg-content">
                <div class="easter-egg-icon">🎉</div>
                <div class="easter-egg-text">
                    <strong>Easter Egg Found!</strong>
                    <p>${egg.name}: ${egg.description}</p>
                    <small>${foundCount}/${Object.keys(EASTER_EGGS).length} found</small>
                </div>
                <button class="easter-egg-close">×</button>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        // Animate in
        setTimeout(() => {
            notification.classList.add('show');
        }, 10);
        
        // Auto-remove after 5 seconds
        const autoRemove = setTimeout(() => {
            removeNotification(notification);
        }, 5000);
        
        // Manual close
        notification.querySelector('.easter-egg-close').addEventListener('click', () => {
            clearTimeout(autoRemove);
            removeNotification(notification);
        });
    }

    function removeNotification(notification) {
        notification.classList.remove('show');
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }

    // Update counter
    function updateCounter() {
        let counter = document.getElementById('easter-egg-counter');
        if (!counter) {
            counter = document.createElement('div');
            counter.id = 'easter-egg-counter';
            counter.style.cssText = `
                position: fixed;
                bottom: 90px;
                right: 30px;
                background: rgba(99, 102, 241, 0.9);
                color: white;
                padding: 8px 16px;
                border-radius: 20px;
                font-size: 0.875rem;
                font-weight: 600;
                z-index: 999;
                cursor: pointer;
                transition: all 0.3s ease;
                box-shadow: 0 4px 15px rgba(99, 102, 241, 0.4);
            `;
            document.body.appendChild(counter);
            
            counter.addEventListener('click', () => {
                showEasterEggList();
            });
        }
        
        counter.textContent = `🎁 ${foundCount}/${Object.keys(EASTER_EGGS).length}`;
        
        if (foundCount === Object.keys(EASTER_EGGS).length) {
            counter.style.background = 'rgba(16, 185, 129, 0.9)';
            counter.textContent = '🎉 All Found!';
        }
    }

    // Show easter egg list
    function showEasterEggList() {
        const modal = document.createElement('div');
        modal.className = 'easter-egg-modal';
        modal.innerHTML = `
            <div class="easter-egg-modal-content">
                <div class="easter-egg-modal-header">
                    <h2>🎁 Easter Eggs</h2>
                    <button class="easter-egg-modal-close">×</button>
                </div>
                <div class="easter-egg-modal-body">
                    <p style="margin-bottom: 1rem; color: var(--text-secondary);">
                        Find all ${Object.keys(EASTER_EGGS).length} easter eggs to get <strong style="color: var(--primary);">1 month of FREE premium!</strong>
                    </p>
                    <p style="margin-bottom: 1rem; color: var(--text-muted); font-size: 0.9rem;">
                        💡 Hint: Just browse normally and interact with the site - they're easy to find!
                    </p>
                    <div class="easter-egg-list">
                        ${Object.entries(EASTER_EGGS).map(([id, egg]) => `
                            <div class="easter-egg-item ${egg.found ? 'found' : ''}">
                                <span class="easter-egg-status">${egg.found ? '✅' : '🔒'}</span>
                                <div class="easter-egg-info">
                                    <strong>${egg.name}</strong>
                                    <small>${egg.description}</small>
                                    ${!egg.found ? `<em>${egg.hint}</em>` : ''}
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        setTimeout(() => {
            modal.classList.add('show');
        }, 10);
        
        modal.querySelector('.easter-egg-modal-close').addEventListener('click', () => {
            modal.classList.remove('show');
            setTimeout(() => {
                if (modal.parentNode) {
                    modal.parentNode.removeChild(modal);
                }
            }, 300);
        });
        
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.classList.remove('show');
                setTimeout(() => {
                    if (modal.parentNode) {
                        modal.parentNode.removeChild(modal);
                    }
                }, 300);
            }
        });
    }

    // Check if all found
    function checkAllFound() {
        if (foundCount === Object.keys(EASTER_EGGS).length) {
            setTimeout(() => {
                const reward = document.createElement('div');
                reward.className = 'easter-egg-reward';
                reward.innerHTML = `
                    <div class="easter-egg-reward-content">
                        <div class="easter-egg-reward-icon">🎉🎁🎉</div>
                        <h2>Congratulations!</h2>
                        <p>You found all easter eggs!</p>
                        <p style="font-size: 1.2rem; color: var(--primary); font-weight: 700; margin: 1rem 0;">
                            You've earned <strong>1 Month of Free Premium!</strong>
                        </p>
                        <p style="color: var(--text-secondary); margin-bottom: 1.5rem;">
                            Your account will be upgraded automatically. Check your profile for details.
                        </p>
                        <button class="btn btn-primary" onclick="this.closest('.easter-egg-reward').remove()">Awesome!</button>
                    </div>
                `;
                document.body.appendChild(reward);
                
                setTimeout(() => {
                    reward.classList.add('show');
                }, 10);
                
                // TODO: Call backend API to grant premium
                grantPremiumReward();
            }, 1000);
        }
    }

    // Grant premium reward (call backend)
    function grantPremiumReward() {
        // This would call your backend API
        fetch('/api/v1/easter-egg/reward', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'same-origin'
        }).catch(err => {
            console.log('Easter egg reward API call (would grant premium)');
        });
    }

    // ============================================
    // EASTER EGG DETECTORS (SIMPLE & FUN!)
    // ============================================

    // 1. Logo Click (3 times - easy!)
    function initLogoClick() {
        const logo = document.querySelector('.navbar-brand img, .navbar-brand');
        if (logo) {
            logo.addEventListener('click', () => {
                logoClickCount++;
                if (logoClickCount >= 3) {
                    saveFoundEgg('logo-click');
                    logoClickCount = 0;
                }
            });
        }
    }

    // 2. Logo Hover
    function initLogoHover() {
        const logo = document.querySelector('.navbar-brand img, .navbar-brand');
        if (logo) {
            logo.addEventListener('mouseenter', () => {
                saveFoundEgg('hover-logo');
            });
        }
    }

    // 3. Scroll to Bottom
    function initScrollToBottom() {
        window.addEventListener('scroll', () => {
            if (scrolledToBottom) return;
            
            const scrollHeight = document.documentElement.scrollHeight;
            const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
            const clientHeight = document.documentElement.clientHeight;
            
            if (scrollTop + clientHeight >= scrollHeight - 50) {
                scrolledToBottom = true;
                saveFoundEgg('scroll-to-bottom');
            }
        });
    }

    // 4. Scroll Halfway
    function initScrollHalfway() {
        window.addEventListener('scroll', () => {
            if (scrolledHalfway) return;
            
            const scrollHeight = document.documentElement.scrollHeight;
            const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
            const scrollPercent = (scrollTop / (scrollHeight - window.innerHeight)) * 100;
            
            if (scrollPercent >= 45 && scrollPercent <= 55) {
                scrolledHalfway = true;
                saveFoundEgg('scroll-halfway');
            }
        });
    }

    // 5. Click Get Started Button
    function initClickHeroButton() {
        document.querySelectorAll('.btn-primary, .btn-secondary').forEach(btn => {
            if (btn.textContent.includes('Get Started') || btn.textContent.includes('Start')) {
                btn.addEventListener('click', () => {
                    saveFoundEgg('click-hero-button');
                });
            }
        });
    }

    // 6. Hover Feature Card
    function initHoverFeatureCard() {
        document.querySelectorAll('.card').forEach(card => {
            card.addEventListener('mouseenter', () => {
                saveFoundEgg('hover-feature-card');
            }, { once: true });
        });
    }

    // 7. Visit Pricing Page
    function initVisitPricing() {
        const pricingLinks = document.querySelectorAll('a[href*="pricing"]');
        pricingLinks.forEach(link => {
            link.addEventListener('click', () => {
                saveFoundEgg('visit-pricing');
            });
        });
        
        // Also check current page
        if (window.location.pathname.includes('pricing')) {
            saveFoundEgg('visit-pricing');
        }
    }

    // 8. Visit Download Page
    function initVisitDownload() {
        const downloadLinks = document.querySelectorAll('a[href*="download"]');
        downloadLinks.forEach(link => {
            link.addEventListener('click', () => {
                saveFoundEgg('visit-download');
            });
        });
        
        // Also check current page
        if (window.location.pathname.includes('download')) {
            saveFoundEgg('visit-download');
        }
    }

    // 9. Click Sign Up
    function initClickSignup() {
        document.querySelectorAll('a[href*="signup"], .btn-primary').forEach(btn => {
            if (btn.textContent.includes('Sign Up') || btn.textContent.includes('Sign Up')) {
                btn.addEventListener('click', () => {
                    saveFoundEgg('click-signup');
                });
            }
        });
    }

    // 10. Click Any CTA
    function initClickCTA() {
        document.querySelectorAll('.btn-primary, .btn-secondary').forEach(btn => {
            btn.addEventListener('click', () => {
                saveFoundEgg('click-cta');
            }, { once: true });
        });
    }

    // Initialize all
    function init() {
        loadFoundEggs();
        initLogoClick();
        initLogoHover();
        initScrollToBottom();
        initScrollHalfway();
        initClickHeroButton();
        initHoverFeatureCard();
        initVisitPricing();
        initVisitDownload();
        initClickSignup();
        initClickCTA();
        
        // Show initial hint after 10 seconds (sooner, more friendly)
        setTimeout(() => {
            if (foundCount === 0) {
                const hint = document.createElement('div');
                hint.className = 'easter-egg-hint';
                hint.innerHTML = `
                    <div class="easter-egg-hint-content">
                        <span>🎁</span>
                        <span>Psst... Find all ${Object.keys(EASTER_EGGS).length} easter eggs for 1 month FREE premium! 🎉</span>
                        <button onclick="this.closest('.easter-egg-hint').remove()">×</button>
                    </div>
                `;
                document.body.appendChild(hint);
                
                setTimeout(() => {
                    hint.classList.add('show');
                }, 10);
                
                setTimeout(() => {
                    hint.classList.remove('show');
                    setTimeout(() => {
                        if (hint.parentNode) {
                            hint.parentNode.removeChild(hint);
                        }
                    }, 300);
                }, 6000);
            }
        }, 10000);
    }

    // Start when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();

