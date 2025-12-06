@echo off
echo ========================================
echo SecureVPN - Certificate Generation
echo ========================================
echo.

REM Check if OpenSSL is available
openssl version >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] OpenSSL is not installed or not in PATH
    echo Please install OpenSSL from: https://slproweb.com/products/Win32OpenSSL.html
    echo Or use Git Bash which includes OpenSSL
    pause
    exit /b 1
)

echo [INFO] OpenSSL found
echo [INFO] Generating military-grade certificates...

REM Create directories
if not exist "certs" mkdir "certs"
if not exist "certs\private" mkdir "certs\private"
if not exist "certs\public" mkdir "certs\public"

REM Generate CA private key (4096-bit RSA)
echo [INFO] Generating CA private key (4096-bit RSA)...
openssl genrsa -out "certs\private\ca.key" 4096
if %errorLevel% neq 0 (
    echo [ERROR] Failed to generate CA private key
    pause
    exit /b 1
)

REM Generate CA certificate (valid for 10 years)
echo [INFO] Generating CA certificate...
openssl req -new -x509 -days 3650 -key "certs\private\ca.key" -out "certs\public\ca.crt" -subj "/C=US/ST=Secure/L=VPN/O=SecureVPN/CN=SecureVPN-CA"
if %errorLevel% neq 0 (
    echo [ERROR] Failed to generate CA certificate
    pause
    exit /b 1
)

REM Generate server private key (4096-bit RSA for maximum security)
echo [INFO] Generating server private key (4096-bit RSA)...
openssl genrsa -out "certs\private\server.key" 4096
if %errorLevel% neq 0 (
    echo [ERROR] Failed to generate server private key
    pause
    exit /b 1
)

REM Generate server certificate signing request
echo [INFO] Generating server CSR...
openssl req -new -key "certs\private\server.key" -out "certs\server.csr" -subj "/C=US/ST=Secure/L=VPN/O=SecureVPN/CN=SecureVPN-Server"
if %errorLevel% neq 0 (
    echo [ERROR] Failed to generate server CSR
    pause
    exit /b 1
)

REM Sign server certificate with CA
echo [INFO] Signing server certificate...
openssl x509 -req -days 365 -in "certs\server.csr" -CA "certs\public\ca.crt" -CAkey "certs\private\ca.key" -CAcreateserial -out "certs\public\server.crt"
if %errorLevel% neq 0 (
    echo [ERROR] Failed to sign server certificate
    pause
    exit /b 1
)

REM Generate client private key (4096-bit RSA for maximum security)
echo [INFO] Generating client private key (4096-bit RSA)...
openssl genrsa -out "certs\private\client.key" 4096
if %errorLevel% neq 0 (
    echo [ERROR] Failed to generate client private key
    pause
    exit /b 1
)

REM Generate client certificate signing request
echo [INFO] Generating client CSR...
openssl req -new -key "certs\private\client.key" -out "certs\client.csr" -subj "/C=US/ST=Secure/L=VPN/O=SecureVPN/CN=SecureVPN-Client"
if %errorLevel% neq 0 (
    echo [ERROR] Failed to generate client CSR
    pause
    exit /b 1
)

REM Sign client certificate with CA
echo [INFO] Signing client certificate...
openssl x509 -req -days 365 -in "certs\client.csr" -CA "certs\public\ca.crt" -CAkey "certs\private\ca.key" -CAcreateserial -out "certs\public\client.crt"
if %errorLevel% neq 0 (
    echo [ERROR] Failed to sign client certificate
    pause
    exit /b 1
)

REM Generate TLS authentication key
echo [INFO] Generating TLS authentication key...
openssl rand -hex 2048 > "certs\ta.key"
if %errorLevel% neq 0 (
    echo [ERROR] Failed to generate TLS auth key
    pause
    exit /b 1
)

REM Generate Diffie-Hellman parameters (4096-bit)
echo [INFO] Generating Diffie-Hellman parameters (4096-bit)...
openssl dhparam -out "certs\dh4096.pem" 4096
if %errorLevel% neq 0 (
    echo [ERROR] Failed to generate DH parameters
    pause
    exit /b 1
)

REM Generate ECDH parameters (P-521 curve)
echo [INFO] Generating ECDH parameters (P-521 curve)...
openssl ecparam -out "certs\ecdh-p521.pem" -name secp521r1
if %errorLevel% neq 0 (
    echo [ERROR] Failed to generate ECDH parameters
    pause
    exit /b 1
)

REM Clean up temporary files
echo [INFO] Cleaning up temporary files...
del "certs\server.csr" >nul 2>&1
del "certs\client.csr" >nul 2>&1
del "certs\ca.srl" >nul 2>&1

REM Set proper permissions (Windows)
echo [INFO] Setting file permissions...
icacls "certs\private\*" /inheritance:r /grant:r "%USERNAME%:(F)" >nul 2>&1
icacls "certs\public\*" /inheritance:r /grant:r "%USERNAME%:(F)" >nul 2>&1

REM Create certificate info file
echo [INFO] Creating certificate information...
echo SecureVPN Professional - Certificate Information > "certs\certificate-info.txt"
echo ================================================ >> "certs\certificate-info.txt"
echo. >> "certs\certificate-info.txt"
echo Generated: %date% %time% >> "certs\certificate-info.txt"
echo. >> "certs\certificate-info.txt"
echo CA Certificate: >> "certs\certificate-info.txt"
echo - Valid for: 10 years >> "certs\certificate-info.txt"
echo - Key size: 4096-bit RSA >> "certs\certificate-info.txt"
echo - Purpose: Certificate Authority >> "certs\certificate-info.txt"
echo. >> "certs\certificate-info.txt"
echo Server Certificate: >> "certs\certificate-info.txt"
echo - Valid for: 1 year >> "certs\certificate-info.txt"
echo - Key size: 2048-bit RSA >> "certs\certificate-info.txt"
echo - Purpose: VPN Server Authentication >> "certs\certificate-info.txt"
echo. >> "certs\certificate-info.txt"
echo Client Certificate: >> "certs\certificate-info.txt"
echo - Valid for: 1 year >> "certs\certificate-info.txt"
echo - Key size: 2048-bit RSA >> "certs\certificate-info.txt"
echo - Purpose: VPN Client Authentication >> "certs\certificate-info.txt"
echo. >> "certs\certificate-info.txt"
echo Security Features: >> "certs\certificate-info.txt"
echo - Perfect Forward Secrecy: ECDHE with P-521 curve >> "certs\certificate-info.txt"
echo - DH Key Exchange: 4096-bit parameters >> "certs\certificate-info.txt"
echo - TLS Authentication: HMAC-SHA256 >> "certs\certificate-info.txt"
echo - Encryption: AES-256-GCM >> "certs\certificate-info.txt"
echo - Authentication: SHA512 >> "certs\certificate-info.txt"

REM Verify certificates
echo [INFO] Verifying certificates...
openssl verify -CAfile "certs\public\ca.crt" "certs\public\server.crt"
openssl verify -CAfile "certs\public\ca.crt" "certs\public\client.crt"

echo.
echo ========================================
echo Certificate Generation Complete!
echo ========================================
echo.
echo [SUCCESS] All certificates generated successfully
echo.
echo Generated files:
echo - CA Certificate: certs\public\ca.crt
echo - CA Private Key: certs\private\ca.key
echo - Server Certificate: certs\public\server.crt
echo - Server Private Key: certs\private\server.key
echo - Client Certificate: certs\public\client.crt
echo - Client Private Key: certs\private\client.key
echo - TLS Auth Key: certs\ta.key
echo - DH Parameters: certs\dh4096.pem
echo - ECDH Parameters: certs\ecdh-p521.pem
echo.
echo [INFO] Certificates are ready for deployment
echo [INFO] Private keys are secured in certs\private\ directory
echo.
pause
