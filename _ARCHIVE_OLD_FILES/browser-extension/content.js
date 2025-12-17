// SecureVPN Privacy Protector - Content Script
// Blocks WebRTC leaks, canvas fingerprinting, and other tracking

(function() {
    'use strict';
    
    // Block WebRTC leaks by overriding RTCPeerConnection
    if (typeof window !== 'undefined') {
        // Backup original if needed
        const OriginalRTCPeerConnection = window.RTCPeerConnection || 
                                          window.webkitRTCPeerConnection || 
                                          window.mozRTCPeerConnection;
        
        if (OriginalRTCPeerConnection) {
            // Override RTCPeerConnection constructor
            window.RTCPeerConnection = function(...args) {
                console.log('[SecureVPN] Blocked WebRTC connection attempt');
                
                // Return a fake/no-op RTCPeerConnection
                return {
                    createDataChannel: () => ({}),
                    createOffer: () => Promise.resolve({}),
                    createAnswer: () => Promise.resolve({}),
                    setLocalDescription: () => Promise.resolve(),
                    setRemoteDescription: () => Promise.resolve(),
                    addIceCandidate: () => Promise.resolve(),
                    close: () => {},
                    getStats: () => Promise.resolve({}),
                    addEventListener: () => {},
                    removeEventListener: () => {},
                    localDescription: null,
                    remoteDescription: null,
                    iceConnectionState: 'closed',
                    connectionState: 'closed',
                    signalingState: 'stable'
                };
            };
            
            // Copy static methods if they exist
            if (OriginalRTCPeerConnection.getDefaultIceServers) {
                window.RTCPeerConnection.getDefaultIceServers = () => [];
            }
        }
        
        // Block getUserMedia (camera/microphone access for fingerprinting)
        const OriginalGetUserMedia = navigator.mediaDevices?.getUserMedia || 
                                     navigator.getUserMedia ||
                                     navigator.webkitGetUserMedia ||
                                     navigator.mozGetUserMedia;
        
        if (OriginalGetUserMedia) {
            if (navigator.mediaDevices) {
                navigator.mediaDevices.getUserMedia = () => {
                    console.log('[SecureVPN] Blocked getUserMedia access');
                    return Promise.reject(new DOMException('Permission denied', 'NotAllowedError'));
                };
            }
            
            navigator.getUserMedia = navigator.webkitGetUserMedia = navigator.mozGetUserMedia = function() {
                console.log('[SecureVPN] Blocked getUserMedia access');
                if (arguments[2]) {
                    arguments[2](new DOMException('Permission denied', 'NotAllowedError'));
                }
            };
        }
        
        // Block canvas fingerprinting
        const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
        const originalGetImageData = CanvasRenderingContext2D.prototype.getImageData;
        
        let canvasNoise = 0;
        
        HTMLCanvasElement.prototype.toDataURL = function() {
            if (this.width > 0 && this.height > 0) {
                const context = this.getContext('2d');
                if (context) {
                    // Add tiny random noise to prevent fingerprinting
                    const imageData = context.getImageData(0, 0, this.width, this.height);
                    for (let i = 0; i < imageData.data.length; i += 4) {
                        canvasNoise = (canvasNoise + 1) % 100;
                        if (canvasNoise < 1) { // Only add noise occasionally
                            imageData.data[i] += Math.floor(Math.random() * 3) - 1;
                        }
                    }
                    context.putImageData(imageData, 0, 0);
                }
            }
            return originalToDataURL.apply(this, arguments);
        };
        
        CanvasRenderingContext2D.prototype.getImageData = function() {
            const imageData = originalGetImageData.apply(this, arguments);
            // Add minimal noise to prevent fingerprinting
            for (let i = 0; i < imageData.data.length; i += 100) {
                imageData.data[i] = (imageData.data[i] + Math.floor(Math.random() * 3) - 1) % 256;
            }
            return imageData;
        };
        
        // Block WebGL fingerprinting
        const originalGetParameter = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(parameter) {
            // Block identifying parameters
            if (parameter === 37445) { // UNMASKED_VENDOR_WEBGL
                return 'SecureVPN';
            }
            if (parameter === 37446) { // UNMASKED_RENDERER_WEBGL
                return 'SecureVPN Renderer';
            }
            return originalGetParameter.apply(this, arguments);
        };
        
        // Block battery API (can be used for fingerprinting)
        if (navigator.getBattery) {
            navigator.getBattery = () => {
                return Promise.resolve({
                    charging: true,
                    chargingTime: 0,
                    dischargingTime: Infinity,
                    level: 1
                });
            };
        }
        
        // Block device orientation/motion (fingerprinting)
        if (window.DeviceMotionEvent) {
            window.DeviceMotionEvent = undefined;
        }
        if (window.DeviceOrientationEvent) {
            window.DeviceOrientationEvent = undefined;
        }
        
        // Randomize timezone offset slightly (make it harder to track)
        const originalGetTimezoneOffset = Date.prototype.getTimezoneOffset;
        const timezoneOffset = originalGetTimezoneOffset.call(new Date());
        Date.prototype.getTimezoneOffset = function() {
            // Return offset with small random variation
            return timezoneOffset + Math.floor(Math.random() * 3) - 1;
        };
        
        console.log('[SecureVPN] Privacy protection enabled');
    }
})();

