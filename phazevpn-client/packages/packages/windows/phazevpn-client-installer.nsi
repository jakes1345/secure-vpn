; PhazeVPN Client NSIS Installer Script
; Requires NSIS (Nullsoft Scriptable Install System)

!define PRODUCT_NAME "PhazeVPN Client"
!define PRODUCT_VERSION "1.0.0"
!define PRODUCT_PUBLISHER "PhazeVPN"
!define PRODUCT_WEB_SITE "https://phazevpn.duckdns.org"
!define PRODUCT_DIR_REGKEY "Software\Microsoft\Windows\CurrentVersion\App Paths\phazevpn-client.exe"
!define PRODUCT_UNINST_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}"
!define PRODUCT_UNINST_ROOT_KEY "HKLM"

; Installer settings
Name "${PRODUCT_NAME} ${PRODUCT_VERSION}"
OutFile "phazevpn-client-setup.exe"
InstallDir "$PROGRAMFILES\PhazeVPN"
RequestExecutionLevel admin
ShowInstDetails show

; Pages
Page directory
Page instfiles

; Install section
Section "MainSection" SEC01
    SetOutPath "$INSTDIR"
    
    ; Copy files
    File "phazevpn-client.py"
    File "requirements.txt"
    
    ; Create launcher
    FileOpen $0 "$INSTDIR\phazevpn-client.bat" w
    FileWrite $0 "@echo off$\r$\n"
    FileWrite $0 "cd /d $\"$INSTDIR$\"$\r$\n"
    FileWrite $0 "python phazevpn-client.py %*$\r$\n"
    FileClose $0
    
    ; Install Python dependencies
    ExecWait 'python -m pip install --quiet requests'
    
    ; Create Start Menu shortcuts
    CreateDirectory "$SMPROGRAMS\PhazeVPN"
    CreateShortCut "$SMPROGRAMS\PhazeVPN\PhazeVPN Client.lnk" "$INSTDIR\phazevpn-client.bat"
    CreateShortCut "$SMPROGRAMS\PhazeVPN\Uninstall.lnk" "$INSTDIR\uninstall.exe"
    
    ; Add to PATH (optional)
    ; EnVar::SetHKLM
    ; EnVar::AddValue "Path" "$INSTDIR"
    
    ; Registry entries
    WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayName" "$(^Name)"
    WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "UninstallString" "$INSTDIR\uninstall.exe"
    WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayVersion" "${PRODUCT_VERSION}"
    WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "URLInfoAbout" "${PRODUCT_WEB_SITE}"
    
    ; Create uninstaller
    WriteUninstaller "$INSTDIR\uninstall.exe"
SectionEnd

; Uninstaller section
Section "Uninstall"
    Delete "$INSTDIR\phazevpn-client.py"
    Delete "$INSTDIR\phazevpn-client.bat"
    Delete "$INSTDIR\requirements.txt"
    Delete "$INSTDIR\uninstall.exe"
    RMDir "$INSTDIR"
    
    Delete "$SMPROGRAMS\PhazeVPN\PhazeVPN Client.lnk"
    Delete "$SMPROGRAMS\PhazeVPN\Uninstall.lnk"
    RMDir "$SMPROGRAMS\PhazeVPN"
    
    DeleteRegKey ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}"
SectionEnd
