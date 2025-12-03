#!/bin/bash
# Fix ttk.Label with fg option on local machine

LOCAL_GUI="/opt/phaze-vpn/vpn-gui.py"

if [ ! -f "$LOCAL_GUI" ]; then
    echo "❌ File not found: $LOCAL_GUI"
    exit 1
fi

echo "Fixing ttk.Label issues in $LOCAL_GUI..."

# Fix info_label, security_label, cert_info - change ttk.Label to tk.Label
sed -i 's/info_label = ttk\.Label(/info_label = tk.Label(/g' "$LOCAL_GUI"
sed -i 's/security_label = ttk\.Label(/security_label = tk.Label(/g' "$LOCAL_GUI"
sed -i 's/cert_info = ttk\.Label(/cert_info = tk.Label(/g' "$LOCAL_GUI"

# Fix phazevpn_frame labels - change ttk.Label to tk.Label
sed -i 's/ttk\.Label(phazevpn_frame, text="⚠️ EXPERIMENTAL:/tk.Label(phazevpn_frame, text="⚠️ EXPERIMENTAL:/g' "$LOCAL_GUI"
sed -i 's/ttk\.Label(phazevpn_frame, text="Uses modern/tk.Label(phazevpn_frame, text="Uses modern/g' "$LOCAL_GUI"
sed -i 's/ttk\.Label(phazevpn_frame, text="For production/tk.Label(phazevpn_frame, text="For production/g' "$LOCAL_GUI"

# Fix phazevpn_frame itself - change ttk.Frame to tk.Frame
sed -i 's/phazevpn_frame = ttk\.Frame(/phazevpn_frame = tk.Frame(/g' "$LOCAL_GUI"

# Fix status_label if it's ttk.Label
sed -i 's/status_label = ttk\.Label(/status_label = tk.Label(/g' "$LOCAL_GUI"

echo "✅ Fixed ttk.Label issues"
echo ""
echo "You can now run: phazevpn-client"

