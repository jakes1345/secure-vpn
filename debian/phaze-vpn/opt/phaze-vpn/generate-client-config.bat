@echo off
echo ========================================
echo SecureVPN - Generate Client Config
echo ========================================
echo.
echo [INFO] Generating OpenVPN client configuration...
echo.

REM Check if certificates exist
if not exist "certs\ca.crt" (
    echo [ERROR] CA certificate not found
    echo [INFO] Run generate-real-certs.bat first
    pause
    exit /b 1
)

if not exist "certs\client.crt" (
    echo [ERROR] Client certificate not found
    echo [INFO] Run generate-real-certs.bat first
    pause
    exit /b 1
)

if not exist "certs\client.key" (
    echo [ERROR] Client private key not found
    echo [INFO] Run generate-real-certs.bat first
    pause
    exit /b 1
)

if not exist "certs\ta.key" (
    echo [ERROR] TLS auth key not found
    echo [INFO] Run generate-real-certs.bat first
    pause
    exit /b 1
)

REM Create client configs directory
if not exist "client-configs" mkdir "client-configs"

echo [INFO] Creating client configuration files...
echo.

REM Get server IP (user input)
set /p SERVER_IP="Enter your server's public IP address: "
if "%SERVER_IP%"=="" (
    echo [ERROR] Server IP required
    pause
    exit /b 1
)

REM Generate client.ovpn
echo [INFO] Generating client.ovpn...
(
echo # SecureVPN Professional - Client Configuration
echo # Generated for: %SERVER_IP%
echo.
echo # Client Configuration
echo client
echo dev tun
echo proto udp
echo remote %SERVER_IP% 1194
echo resolv-retry infinite
echo nobind
echo.
echo # Maximum Security Settings - Beyond AES-256
echo data-ciphers CHACHA20-POLY1305:AES-256-GCM
echo cipher CHACHA20-POLY1305
echo auth SHA512
echo tls-version-min 1.3
echo.
echo # Certificate Files (embedded)
echo <ca>
type "certs\ca.crt"
echo </ca>
echo.
echo <cert>
type "certs\client.crt"
echo </cert>
echo.
echo <key>
type "certs\client.key"
echo </key>
echo.
echo <tls-auth>
type "certs\ta.key"
echo </tls-auth>
echo key-direction 1
echo.
echo # Performance Settings
echo tun-mtu 1500
echo mssfix 1450
echo fragment 1400
echo.
echo # Security Features
echo auth-nocache
echo reneg-sec 0
echo.
echo # DNS Protection
echo block-outside-dns
echo.
echo # Logging
echo verb 3
echo.
echo # Connection Settings
echo persist-key
echo persist-tun
echo keepalive 10 120
echo comp-lzo no
) > "client-configs\client.ovpn"

echo [OK] client.ovpn generated

REM Generate Windows client config
echo [INFO] Generating Windows client config...
(
echo # SecureVPN Professional - Windows Client
echo # Generated for: %SERVER_IP%
echo.
echo # Client Configuration
echo client
echo dev tun
echo proto udp
echo remote %SERVER_IP% 1194
echo resolv-retry infinite
echo nobind
echo.
echo # Maximum Security Settings - Beyond AES-256
echo data-ciphers CHACHA20-POLY1305:AES-256-GCM
echo cipher CHACHA20-POLY1305
echo auth SHA512
echo tls-version-min 1.3
echo.
echo # Certificate Files (embedded)
echo <ca>
type "certs\ca.crt"
echo </ca>
echo.
echo <cert>
type "certs\client.crt"
echo </cert>
echo.
echo <key>
type "certs\client.key"
echo </key>
echo.
echo <tls-auth>
type "certs\ta.key"
echo </tls-auth>
echo key-direction 1
echo.
echo # Windows-specific Settings
echo route-method exe
echo route-delay 2
echo.
echo # Performance Settings
echo tun-mtu 1500
echo mssfix 1450
echo fragment 1400
echo.
echo # Security Features
echo auth-nocache
echo reneg-sec 0
echo.
echo # DNS Protection
echo block-outside-dns
echo.
echo # Logging
echo verb 3
echo.
echo # Connection Settings
echo persist-key
echo persist-tun
echo keepalive 10 120
echo comp-lzo no
) > "client-configs\windows-client.ovpn"

echo [OK] windows-client.ovpn generated

REM Generate mobile client config
echo [INFO] Generating mobile client config...
(
echo # SecureVPN Professional - Mobile Client
echo # Generated for: %SERVER_IP%
echo.
echo # Client Configuration
echo client
echo dev tun
echo proto udp
echo remote %SERVER_IP% 1194
echo resolv-retry infinite
echo nobind
echo.
echo # Maximum Security Settings - Beyond AES-256
echo data-ciphers CHACHA20-POLY1305:AES-256-GCM
echo cipher CHACHA20-POLY1305
echo auth SHA512
echo tls-version-min 1.3
echo.
echo # Certificate Files (embedded)
echo <ca>
type "certs\ca.crt"
echo </ca>
echo.
echo <cert>
type "certs\client.crt"
echo </cert>
echo.
echo <key>
type "certs\client.key"
echo </key>
echo.
echo <tls-auth>
type "certs\ta.key"
echo </tls-auth>
echo key-direction 1
echo.
echo # Mobile-specific Settings
echo float
echo.
echo # Performance Settings
echo tun-mtu 1500
echo mssfix 1450
echo fragment 1400
echo.
echo # Security Features
echo auth-nocache
echo reneg-sec 0
echo.
echo # DNS Protection
echo block-outside-dns
echo.
echo # Logging
echo verb 2
echo.
echo # Connection Settings
echo persist-key
echo persist-tun
echo keepalive 10 120
echo comp-lzo no
) > "client-configs\mobile-client.ovpn"

echo [OK] mobile-client.ovpn generated

echo.
echo ========================================
echo Client Configuration Complete!
echo ========================================
echo.
echo [OK] Generated client configurations:
echo.
echo [Windows] client-configs\windows-client.ovpn
echo [Universal] client-configs\client.ovpn
echo [Mobile] client-configs\mobile-client.ovpn
echo.
echo [INFO] To use these configs:
echo 1. Copy the .ovpn file to your device
echo 2. Import into OpenVPN client
echo 3. Connect to %SERVER_IP%:1194
echo.
echo [INFO] Server IP: %SERVER_IP%
echo [INFO] Port: 1194
echo [INFO] Protocol: UDP
echo [INFO] Encryption: ChaCha20-Poly1305 (beyond AES-256) + SHA512
echo.

pause
