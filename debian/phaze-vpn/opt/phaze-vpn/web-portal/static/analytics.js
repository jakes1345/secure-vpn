// PhazeVPN Analytics
// Privacy-friendly analytics (optional - can be disabled)

(function() {
    // Only load if user hasn't opted out
    if (localStorage.getItem('analytics_opt_out') === 'true') {
        return;
    }
    
    // Basic page view tracking (no personal data)
    function trackPageView() {
        // Send to your analytics endpoint (if you set one up)
        // For now, just log locally
        console.log('Page view:', window.location.pathname);
    }
    
    // Track on page load
    if (document.readyState === 'complete') {
        trackPageView();
    } else {
        window.addEventListener('load', trackPageView);
    }
})();

