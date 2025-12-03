#!/bin/bash
# Build RPM package for Fedora/RedHat/CentOS

set -e

PACKAGE_NAME="phazevpn-client"
VERSION="1.0.0"
RELEASE="1"

echo "Building RPM package..."

# Create RPM build directories
RPM_DIR="rpm-build"
rm -rf $RPM_DIR
mkdir -p $RPM_DIR/{BUILD,BUILDROOT,RPMS,SOURCES,SPECS,SRPMS}

# Copy source
cp phazevpn-client.py $RPM_DIR/SOURCES/

# Create spec file
cat > $RPM_DIR/SPECS/${PACKAGE_NAME}.spec << EOF
Name:           $PACKAGE_NAME
Version:        $VERSION
Release:        $RELEASE%{?dist}
Summary:        PhazeVPN Secure VPN Client
License:        Proprietary
URL:            https://phazevpn.duckdns.org
Source0:        phazevpn-client.py

Requires:       python3 python3-requests openvpn

%description
Professional VPN client with automatic configuration
and one-click connectivity.

%prep
cp %{SOURCE0} .

%build
# No build needed for Python script

%install
mkdir -p %{buildroot}/usr/bin
install -m 755 phazevpn-client.py %{buildroot}/usr/bin/phazevpn-client

mkdir -p %{buildroot}/usr/share/applications
cat > %{buildroot}/usr/share/applications/phazevpn-client.desktop << DESKTOP
[Desktop Entry]
Name=PhazeVPN Client
Exec=/usr/bin/phazevpn-client
Terminal=false
Type=Application
Categories=Network;
DESKTOP

%files
/usr/bin/phazevpn-client
/usr/share/applications/phazevpn-client.desktop

%changelog
* $(date '+%a %b %d %Y') PhazeVPN <support@phazevpn.duckdns.org> - $VERSION-$RELEASE
- Initial release
EOF

# Build RPM
rpmbuild --define "_topdir $(pwd)/$RPM_DIR" -bb $RPM_DIR/SPECS/${PACKAGE_NAME}.spec

# Copy to installers
cp $RPM_DIR/RPMS/*/${PACKAGE_NAME}-${VERSION}-${RELEASE}.*.rpm installers/ 2>/dev/null || true

echo "✅ RPM package created in installers/ directory"

