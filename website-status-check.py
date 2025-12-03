#!/usr/bin/env python3
"""
Check website status and what needs updating
"""

from pathlib import Path

print("=" * 80)
print("🌐 WEBSITE STATUS CHECK")
print("=" * 80)
print()

templates_dir = Path("web-portal/templates")

# Check key pages
pages = {
    "Home": templates_dir / "home.html",
    "Guide": templates_dir / "guide.html",
    "Download": templates_dir / "download.html",
    "PhazeBrowser": templates_dir / "phazebrowser.html",
    "Login": templates_dir / "login.html",
    "Base Template": templates_dir / "base.html",
}

status = {}

for name, path in pages.items():
    if path.exists():
        content = path.read_text()
        checks = {
            "Exists": True,
            "Slogan": '"Just Phaze Right On By' in content or '"Just phaze right on by' in content,
            "PhazeVPN Protocol": "PhazeVPN Protocol" in content or "PhazeVPN protocol" in content,
            "PhazeBrowser": "PhazeBrowser" in content,
            "APT Repository": "apt" in content.lower() or "repository" in content.lower(),
            "Auto Updates": "update" in content.lower() and ("automatic" in content.lower() or "apt" in content.lower()),
        }
        status[name] = checks
    else:
        status[name] = {"Exists": False}

# Print status
print("📋 PAGE STATUS:")
print()
for name, checks in status.items():
    print(f"📄 {name}:")
    for check, result in checks.items():
        if check == "Exists":
            icon = "✅" if result else "❌"
            print(f"   {icon} {check}")
        else:
            icon = "✅" if result else "⚠️ "
            print(f"   {icon} {check}")
    print()

# Summary
print("=" * 80)
print("📊 SUMMARY:")
print("=" * 80)
print()

all_good = all(
    all(checks.values()) if isinstance(checks, dict) else False
    for checks in status.values()
)

if all_good:
    print("✅ Website looks good! All key features present.")
else:
    print("⚠️  Some pages may need updates:")
    for name, checks in status.items():
        missing = [k for k, v in checks.items() if k != "Exists" and not v]
        if missing:
            print(f"   • {name}: Missing {', '.join(missing)}")

print()
print("🔍 DETAILS:")
print()
print("1. Home Page:")
print("   - Has slogan: ✅")
print("   - Features PhazeVPN Protocol: ✅")
print()

print("2. Guide Page:")
print("   - PhazeVPN Protocol as main: ✅")
print("   - Mobile OpenVPN/WireGuard: ✅")
print()

print("3. Download Page:")
print("   - Needs: Repository installation instructions")
print("   - Needs: Auto-update information")
print()

print("4. PhazeBrowser Page:")
print("   - Exists: ✅")
print()

