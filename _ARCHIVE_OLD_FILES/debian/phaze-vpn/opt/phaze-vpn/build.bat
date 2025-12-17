@echo off
echo ========================================
echo SecureVPN Professional - Build Script
echo ========================================
echo.

REM Check if .NET 6.0 is installed
dotnet --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] .NET 6.0 SDK is not installed
    echo Please install .NET 6.0 SDK from: https://dotnet.microsoft.com/download
    pause
    exit /b 1
)

echo [INFO] .NET 6.0 SDK found
echo [INFO] Building SecureVPN Professional Client...

REM Clean previous builds
if exist "bin" rmdir /s /q "bin"
if exist "obj" rmdir /s /q "obj"

REM Restore NuGet packages
echo [INFO] Restoring NuGet packages...
dotnet restore SecureVPNClient.csproj

REM Build the application
echo [INFO] Building application...
dotnet build SecureVPNClient.csproj --configuration Release --no-restore

if %errorLevel% neq 0 (
    echo [ERROR] Build failed
    pause
    exit /b 1
)

REM Publish the application
echo [INFO] Publishing application...
dotnet publish SecureVPNClient.csproj --configuration Release --output "bin\Release\net6.0-windows\publish" --self-contained true --runtime win-x64 --publish-single-file true

if %errorLevel% neq 0 (
    echo [ERROR] Publish failed
    pause
    exit /b 1
)

REM Copy configuration files
echo [INFO] Copying configuration files...
if not exist "bin\Release\net6.0-windows\publish\config" mkdir "bin\Release\net6.0-windows\publish\config"
copy "config\*" "bin\Release\net6.0-windows\publish\config\" /Y >nul 2>&1

REM Copy scripts
if not exist "bin\Release\net6.0-windows\publish\scripts" mkdir "bin\Release\net6.0-windows\publish\scripts"
copy "scripts\*" "bin\Release\net6.0-windows\publish\scripts\" /Y >nul 2>&1

REM Copy certificates directory
if not exist "bin\Release\net6.0-windows\publish\certs" mkdir "bin\Release\net6.0-windows\publish\certs"
if exist "certs\*" copy "certs\*" "bin\Release\net6.0-windows\publish\certs\" /Y >nul 2>&1

REM Create deployment package
echo [INFO] Creating deployment package...
if not exist "deploy" mkdir "deploy"
xcopy "bin\Release\net6.0-windows\publish\*" "deploy\" /E /I /Y >nul 2>&1

REM Copy installer
copy "install.bat" "deploy\" /Y >nul 2>&1
copy "README.md" "deploy\" /Y >nul 2>&1

REM Create deployment script
echo @echo off > "deploy\deploy.bat"
echo echo Installing SecureVPN Professional... >> "deploy\deploy.bat"
echo echo. >> "deploy\deploy.bat"
echo echo This will install SecureVPN on your system. >> "deploy\deploy.bat"
echo echo Please run as Administrator. >> "deploy\deploy.bat"
echo echo. >> "deploy\deploy.bat"
echo pause >> "deploy\deploy.bat"
echo call install.bat >> "deploy\deploy.bat"

echo.
echo ========================================
echo Build Completed Successfully!
echo ========================================
echo.
echo [SUCCESS] SecureVPN Professional has been built
echo.
echo Build output: bin\Release\net6.0-windows\publish\
echo Deployment package: deploy\
echo.
echo [INFO] To install, run deploy\deploy.bat as Administrator
echo [INFO] To run locally, use bin\Release\net6.0-windows\publish\SecureVPNClient.exe
echo.
pause
