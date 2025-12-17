#include "privacyengine.h"
#include <QWebEngineScript>
#include <QWebEngineScriptCollection>
#include <QFile>
#include <QTextStream>
#include <QJsonDocument>
#include <QJsonArray>
#include <QStandardPaths>
#include <QDir>

PrivacyEngine::PrivacyEngine(QObject *parent)
    : QObject(parent)
    , m_adBlocking(true)
    , m_trackingProtection(true)
    , m_fingerprintProtection(true)
    , m_cookieBlocking(true)
    , m_blockAllCookies(true)
    , m_blockFonts(true)
    , m_blockCamera(true)
    , m_blockMicrophone(true)
    , m_blockGeolocation(true)
    , m_blockNotifications(true)
    , m_adsBlocked(0)
    , m_trackersBlocked(0)
    , m_cookiesBlocked(0)
    , m_requestsBlocked(0)
{
    // Initialize blocked domains
    m_blockedDomains = QStringList({
        "doubleclick.net", "googlesyndication.com", "googleadservices.com",
        "adsense.com", "adform.com", "adnxs.com", "adsrvr.org", "adtechus.com",
        "criteo.com", "rubiconproject.com", "pubmatic.com", "openx.net",
        "indexexchange.com", "33across.com", "outbrain.com", "taboola.com",
        "revcontent.com", "zemanta.com", "content.ad", "adsystem.com",
        "google-analytics.com", "googletagmanager.com", "facebook.net",
        "facebook.com/tr", "scorecardresearch.com", "quantserve.com",
        "chartbeat.com", "mixpanel.com", "segment.com", "amplitude.com",
        "hotjar.com", "fullstory.com", "mouseflow.com", "crazyegg.com",
        "optimizely.com", "vwo.com", "newrelic.com", "addthis.com",
        "sharethis.com", "addtoany.com", "bluekai.com", "lotame.com",
        "neustar.biz", "exelate.com", "turn.com", "amazon-adsystem.com"
    });
    
    // Ad patterns
    m_adPatterns = QStringList({
        "doubleclick", "googlesyndication", "googleadservices", "adsense",
        "adform", "adnxs", "adsrvr", "adtech", "criteo", "rubiconproject",
        "pubmatic", "openx", "indexexchange", "33across", "outbrain",
        "taboola", "revcontent", "zemanta", "content.ad", "adsystem",
        "/ads/", "/advertising/", "/banner", "/sponsor", "/promo",
        "/ad.", ".ad.", "/ad?", "?ad=", "/ad/", "/ads?",
        "advertisement", "advert", "sponsored", "promotion"
    });
    
    // Tracking domains
    m_trackingDomains = QStringList({
        "google-analytics.com", "googletagmanager.com", "googleadservices.com",
        "googlesyndication.com", "doubleclick.net", "adservice.google",
        "analytics.google", "facebook.net", "facebook.com/tr", "fbcdn.net",
        "connect.facebook.net", "twitter.com/i/adsct", "ads-twitter.com",
        "amazon-adsystem.com", "scorecardresearch.com", "quantserve.com",
        "chartbeat.com", "mixpanel.com", "segment.com", "amplitude.com",
        "hotjar.com", "fullstory.com", "mouseflow.com", "crazyegg.com",
        "optimizely.com", "vwo.com", "newrelic.com", "adobe", "omniture",
        "addthis.com", "sharethis.com", "addtoany.com", "bluekai.com",
        "lotame.com", "neustar.biz", "exelate.com", "turn.com"
    });
}

void PrivacyEngine::applyPrivacySettings(QWebEngineView *webView)
{
    QWebEngineSettings *settings = webView->settings();
    
    // Privacy settings
    settings->setAttribute(QWebEngineSettings::JavascriptEnabled, true);
    settings->setAttribute(QWebEngineSettings::PluginsEnabled, false);
    settings->setAttribute(QWebEngineSettings::LocalStorageEnabled, false);
    settings->setAttribute(QWebEngineSettings::JavascriptCanOpenWindows, false);
    settings->setAttribute(QWebEngineSettings::JavascriptCanAccessClipboard, false);
    
    // Media access
    // Note: Qt6 WebEngine handles media permissions differently
    // Media blocking is handled via JavaScript injection in injectFingerprintProtection
    
    // Apply injections
    if (m_adBlocking) {
        injectAdBlocking(webView);
    }
    
    if (m_trackingProtection) {
        injectTrackingProtection(webView);
    }
    
    if (m_fingerprintProtection) {
        injectFingerprintProtection(webView);
    }
    
    if (m_cookieBlocking) {
        injectCookieBlocking(webView);
    }
    
    if (m_blockFonts) {
        // Inject font blocking CSS
        QWebEngineScript script;
        script.setSourceCode(getFontBlockingCSS());
        script.setInjectionPoint(QWebEngineScript::DocumentReady);
        script.setWorldId(QWebEngineScript::MainWorld);
        webView->page()->scripts().insert(script);
    }
}

void PrivacyEngine::injectAdBlocking(QWebEngineView *webView)
{
    QWebEngineScript script;
    script.setSourceCode(getAdBlockingJS());
    script.setInjectionPoint(QWebEngineScript::DocumentCreation);
    script.setWorldId(QWebEngineScript::MainWorld);
    webView->page()->scripts().insert(script);
}

void PrivacyEngine::injectTrackingProtection(QWebEngineView *webView)
{
    QWebEngineScript script;
    script.setSourceCode(getTrackingProtectionJS());
    script.setInjectionPoint(QWebEngineScript::DocumentCreation);
    script.setWorldId(QWebEngineScript::MainWorld);
    webView->page()->scripts().insert(script);
}

void PrivacyEngine::injectFingerprintProtection(QWebEngineView *webView)
{
    QWebEngineScript script;
    script.setSourceCode(getFingerprintProtectionJS());
    script.setInjectionPoint(QWebEngineScript::DocumentCreation);
    script.setWorldId(QWebEngineScript::MainWorld);
    webView->page()->scripts().insert(script);
}

void PrivacyEngine::injectCookieBlocking(QWebEngineView *webView)
{
    QWebEngineScript script;
    script.setSourceCode(getCookieBlockingJS());
    script.setInjectionPoint(QWebEngineScript::DocumentCreation);
    script.setWorldId(QWebEngineScript::MainWorld);
    webView->page()->scripts().insert(script);
}

QString PrivacyEngine::getAdBlockingJS()
{
    QStringList patterns;
    for (const QString &pattern : m_adPatterns) {
        patterns << QString("\"%1\"").arg(pattern);
    }
    
    return QString(R"(
        (function() {
            'use strict';
            const adPatterns = [%1];
            
            function isAdElement(element) {
                if (!element) return false;
                const className = element.className || '';
                const id = element.id || '';
                const src = element.src || '';
                const href = element.href || '';
                const text = (className + ' ' + id + ' ' + src + ' ' + href).toLowerCase();
                return adPatterns.some(pattern => text.includes(pattern));
            }
            
            function removeAds() {
                const allElements = document.querySelectorAll('*');
                allElements.forEach(element => {
                    if (isAdElement(element)) {
                        element.style.display = 'none';
                        element.style.visibility = 'hidden';
                        element.remove();
                    }
                });
                
                const iframes = document.querySelectorAll('iframe');
                iframes.forEach(iframe => {
                    const src = iframe.src || '';
                    if (adPatterns.some(pattern => src.includes(pattern))) {
                        iframe.remove();
                    }
                });
            }
            
            removeAds();
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', removeAds);
            }
            
            const observer = new MutationObserver(function(mutations) {
                mutations.forEach(function(mutation) {
                    mutation.addedNodes.forEach(function(node) {
                        if (node.nodeType === 1 && isAdElement(node)) {
                            node.remove();
                        }
                    });
                });
            });
            observer.observe(document.body || document.documentElement, {
                childList: true,
                subtree: true
            });
            
            const originalFetch = window.fetch;
            window.fetch = function(...args) {
                const url = args[0];
                if (typeof url === 'string' && adPatterns.some(pattern => url.includes(pattern))) {
                    return Promise.resolve(new Response('', { status: 200 }));
                }
                return originalFetch.apply(this, args);
            };
        })();
    )").arg(patterns.join(", "));
}

QString PrivacyEngine::getTrackingProtectionJS()
{
    QStringList domains;
    for (const QString &domain : m_trackingDomains) {
        domains << QString("\"%1\"").arg(domain);
    }
    
    return QString(R"(
        (function() {
            'use strict';
            const trackingDomains = [%1];
            
            function isTrackingDomain(url) {
                if (!url) return false;
                const urlLower = url.toLowerCase();
                return trackingDomains.some(domain => urlLower.includes(domain));
            }
            
            function blockTracking() {
                const scripts = document.getElementsByTagName('script');
                for (let script of scripts) {
                    if (script.src && isTrackingDomain(script.src)) {
                        script.remove();
                    }
                }
                
                const imgs = document.getElementsByTagName('img');
                for (let img of imgs) {
                    if (img.src && isTrackingDomain(img.src)) {
                        img.remove();
                    }
                }
                
                const iframes = document.getElementsByTagName('iframe');
                for (let iframe of iframes) {
                    if (iframe.src && isTrackingDomain(iframe.src)) {
                        iframe.remove();
                    }
                }
            }
            
            blockTracking();
            
            const observer = new MutationObserver(function(mutations) {
                mutations.forEach(function(mutation) {
                    mutation.addedNodes.forEach(function(node) {
                        if (node.nodeType === 1) {
                            if (node.tagName === 'SCRIPT' && node.src && isTrackingDomain(node.src)) {
                                node.remove();
                            }
                            if (node.tagName === 'IMG' && node.src && isTrackingDomain(node.src)) {
                                node.remove();
                            }
                            if (node.tagName === 'IFRAME' && node.src && isTrackingDomain(node.src)) {
                                node.remove();
                            }
                        }
                    });
                });
            });
            observer.observe(document.body || document.documentElement, {
                childList: true,
                subtree: true
            });
            
            const originalFetch = window.fetch;
            window.fetch = function(...args) {
                const url = args[0];
                if (typeof url === 'string' && isTrackingDomain(url)) {
                    return Promise.reject(new Error('Tracking blocked'));
                }
                return originalFetch.apply(this, args);
            };
        })();
    )").arg(domains.join(", "));
}

QString PrivacyEngine::getFingerprintProtectionJS()
{
    return QString(R"(
        (function() {
            'use strict';
            
            // Canvas fingerprinting protection
            const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
            HTMLCanvasElement.prototype.toDataURL = function() {
                const context = this.getContext('2d');
                if (context) {
                    const imageData = context.getImageData(0, 0, this.width, this.height);
                    for (let i = 0; i < imageData.data.length; i += 4) {
                        imageData.data[i] += Math.random() * 0.01;
                    }
                    context.putImageData(imageData, 0, 0);
                }
                return originalToDataURL.apply(this, arguments);
            };
            
            // WebGL fingerprinting protection
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {
                if (parameter === 37445) return 'Intel Inc.';
                if (parameter === 37446) return 'Intel Iris OpenGL Engine';
                return getParameter.apply(this, arguments);
            };
            
            // Screen fingerprinting protection
            Object.defineProperty(window.screen, 'width', {
                get: function() { return 1920; },
                configurable: true
            });
            Object.defineProperty(window.screen, 'height', {
                get: function() { return 1080; },
                configurable: true
            });
            
            // Navigator fingerprinting protection
            Object.defineProperty(navigator, 'platform', {
                get: function() { return 'Linux x86_64'; },
                configurable: true
            });
            Object.defineProperty(navigator, 'hardwareConcurrency', {
                get: function() { return 4; },
                configurable: true
            });
            
            // WebRTC leak protection
            if (window.RTCPeerConnection) {
                window.RTCPeerConnection = function() {
                    throw new Error('WebRTC blocked');
                };
            }
            
            // Battery API protection
            if (navigator.getBattery) {
                navigator.getBattery = function() {
                    return Promise.resolve({
                        charging: true,
                        chargingTime: 0,
                        dischargingTime: Infinity,
                        level: 1
                    });
                };
            }
            
            // Permissions API protection
            if (navigator.permissions) {
                const originalQuery = navigator.permissions.query;
                navigator.permissions.query = function(descriptor) {
                    if (descriptor.name === 'notifications' || 
                        descriptor.name === 'geolocation' ||
                        descriptor.name === 'camera' ||
                        descriptor.name === 'microphone') {
                        return Promise.resolve({ state: 'denied' });
                    }
                    return originalQuery.apply(this, arguments);
                };
            }
        })();
    )");
}

QString PrivacyEngine::getCookieBlockingJS()
{
    QStringList domains;
    for (const QString &domain : m_trackingDomains) {
        domains << QString("\"%1\"").arg(domain);
    }
    
    QString blockAll = m_blockAllCookies ? "true" : "false";
    
    return QString(R"(
        (function() {
            'use strict';
            const trackingDomains = [%1];
            const BLOCK_ALL_COOKIES = %2;
            
            function isTrackingDomain(domain) {
                if (!domain) return false;
                const domainLower = domain.toLowerCase();
                return trackingDomains.some(td => domainLower.includes(td));
            }
            
            const originalCookieDescriptor = Object.getOwnPropertyDescriptor(Document.prototype, 'cookie') ||
                                            Object.getOwnPropertyDescriptor(HTMLDocument.prototype, 'cookie');
            
            if (originalCookieDescriptor && originalCookieDescriptor.set) {
                Object.defineProperty(Document.prototype, 'cookie', {
                    get: function() {
                        if (BLOCK_ALL_COOKIES) return '';
                        const cookies = originalCookieDescriptor.get.call(this);
                        return cookies.split(';').filter(cookie => {
                            return !isTrackingDomain(cookie);
                        }).join(';');
                    },
                    set: function(value) {
                        if (BLOCK_ALL_COOKIES) return;
                        if (isTrackingDomain(value)) return;
                        return originalCookieDescriptor.set.call(this, value);
                    },
                    configurable: true
                });
            }
            
            // Block localStorage
            const originalSetItem = Storage.prototype.setItem;
            Storage.prototype.setItem = function(key, value) {
                if (BLOCK_ALL_COOKIES || isTrackingDomain(key) || isTrackingDomain(value)) {
                    return;
                }
                return originalSetItem.apply(this, arguments);
            };
            
            // Block sessionStorage
            const originalSessionSetItem = sessionStorage.setItem;
            sessionStorage.setItem = function(key, value) {
                if (BLOCK_ALL_COOKIES || isTrackingDomain(key) || isTrackingDomain(value)) {
                    return;
                }
                return originalSessionSetItem.apply(this, arguments);
            };
        })();
    )").arg(domains.join(", ")).arg(blockAll);
}

QString PrivacyEngine::getFontBlockingCSS()
{
    return QString(R"(
        @font-face {
            font-family: 'blocked' !important;
        }
        * {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
        }
    )");
}

void PrivacyEngine::setAdBlocking(bool enabled) { m_adBlocking = enabled; }
void PrivacyEngine::setTrackingProtection(bool enabled) { m_trackingProtection = enabled; }
void PrivacyEngine::setFingerprintProtection(bool enabled) { m_fingerprintProtection = enabled; }
void PrivacyEngine::setCookieBlocking(bool enabled) { m_cookieBlocking = enabled; }
void PrivacyEngine::setBlockAllCookies(bool enabled) { m_blockAllCookies = enabled; }
void PrivacyEngine::setBlockFonts(bool enabled) { m_blockFonts = enabled; }
void PrivacyEngine::setBlockCamera(bool enabled) { m_blockCamera = enabled; }
void PrivacyEngine::setBlockMicrophone(bool enabled) { m_blockMicrophone = enabled; }
void PrivacyEngine::setBlockGeolocation(bool enabled) { m_blockGeolocation = enabled; }
void PrivacyEngine::setBlockNotifications(bool enabled) { m_blockNotifications = enabled; }

QJsonObject PrivacyEngine::getPrivacyStats() const
{
    QJsonObject stats;
    stats["adsBlocked"] = m_adsBlocked;
    stats["trackersBlocked"] = m_trackersBlocked;
    stats["cookiesBlocked"] = m_cookiesBlocked;
    stats["requestsBlocked"] = m_requestsBlocked;
    stats["domainsBlocked"] = static_cast<int>(m_domainsBlocked.size());
    return stats;
}

void PrivacyEngine::resetStats()
{
    m_adsBlocked = 0;
    m_trackersBlocked = 0;
    m_cookiesBlocked = 0;
    m_requestsBlocked = 0;
    m_domainsBlocked.clear();
}
