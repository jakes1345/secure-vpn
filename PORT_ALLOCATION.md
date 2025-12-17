# 🔌 PHAZE ECOSYSTEM - PORT ALLOCATION
## Proper Port Assignment for All Services

---

## 📊 **PORT ALLOCATION TABLE**

### **VPN Protocols**
```
WireGuard:     51820/UDP  (standard WireGuard port)
OpenVPN:       1194/UDP   (standard OpenVPN port)
PhazeVPN:      51821/UDP  (custom protocol, different from WireGuard)
```

### **Web Services**
```
HTTP:          80/TCP     (Nginx - redirect to HTTPS)
HTTPS:         443/TCP    (Nginx - SSL)
Web Portal:    5000/TCP   (Flask - internal, proxied by Nginx)
Email API:     5005/TCP   (Flask - internal)
```

### **Database & Cache**
```
MySQL:         3306/TCP   (localhost only)
Redis:         6379/TCP   (localhost only)
```

### **Management**
```
SSH:           22/TCP     (server management)
```

---

## 🔧 **VPS FIREWALL CONFIGURATION**

### **Required UFW Rules:**
```bash
# Allow SSH
ufw allow 22/tcp

# Allow HTTP/HTTPS
ufw allow 80/tcp
ufw allow 443/tcp

# Allow VPN protocols
ufw allow 51820/udp  # WireGuard
ufw allow 1194/udp   # OpenVPN
ufw allow 51821/udp  # PhazeVPN

# Enable firewall
ufw enable
```

---

## 📋 **SERVICE CONFIGURATIONS**

### **WireGuard** (Port 51820)
```ini
# /etc/wireguard/wg0.conf
[Interface]
Address = 10.7.0.1/24
ListenPort = 51820
PrivateKey = <server_private_key>
```

### **OpenVPN** (Port 1194)
```conf
# /etc/openvpn/server.conf
port 1194
proto udp
dev tun
server 10.8.0.0 255.255.255.0
```

### **PhazeVPN** (Port 51821)
```bash
# /usr/local/bin/phazevpn-server
./phazevpn-server --host 0.0.0.0 --port 51821 --network 10.9.0.0/24
```

---

## 🌐 **CLIENT CONFIGURATIONS**

### **WireGuard Client**
```ini
[Interface]
PrivateKey = <client_private_key>
Address = 10.7.0.2/24

[Peer]
PublicKey = <server_public_key>
Endpoint = 15.204.11.19:51820
AllowedIPs = 0.0.0.0/0
```

### **OpenVPN Client**
```conf
client
remote 15.204.11.19 1194
proto udp
dev tun
```

### **PhazeVPN Client**
```ini
[Client]
ServerAddress = 15.204.11.19:51821
Network = 10.9.0.0/24
```

---

## 🎯 **NETWORK RANGES**

### **VPN Networks (Non-Overlapping)**
```
WireGuard:  10.7.0.0/24   (10.7.0.1 - 10.7.0.254)
OpenVPN:    10.8.0.0/24   (10.8.0.1 - 10.8.0.254)
PhazeVPN:   10.9.0.0/24   (10.9.0.1 - 10.9.0.254)
```

### **Why Different Networks:**
- Prevents IP conflicts
- Allows running all 3 simultaneously
- Users can switch protocols without disconnect
- Easier routing and debugging

---

## 🔒 **SECURITY CONSIDERATIONS**

### **Port Separation Benefits:**
```
✅ No port conflicts
✅ Can run all protocols simultaneously
✅ Easy to firewall specific protocols
✅ Clear traffic separation
✅ Independent monitoring
```

### **Firewall Rules:**
```bash
# Allow only VPN ports
iptables -A INPUT -p udp --dport 51820 -j ACCEPT  # WireGuard
iptables -A INPUT -p udp --dport 1194 -j ACCEPT   # OpenVPN
iptables -A INPUT -p udp --dport 51821 -j ACCEPT  # PhazeVPN

# Drop all other UDP
iptables -A INPUT -p udp -j DROP
```

---

## 📊 **CURRENT VPS STATUS**

### **What's Actually Running:**
```
✅ OpenVPN:  Port 1194 (ACTIVE)
⚠️ WireGuard: Port 51820 (CONFIGURED, NOT RUNNING)
❌ PhazeVPN:  Port 51821 (NOT CONFIGURED)
```

### **What Needs to Be Done:**
```
1. Start WireGuard on port 51820
2. Configure PhazeVPN on port 51821
3. Update firewall rules
4. Test all 3 protocols
```

---

## 🚀 **DEPLOYMENT COMMANDS**

### **1. Configure Firewall:**
```bash
ssh root@15.204.11.19 "
ufw allow 51820/udp comment 'WireGuard'
ufw allow 1194/udp comment 'OpenVPN'
ufw allow 51821/udp comment 'PhazeVPN'
ufw reload
"
```

### **2. Start WireGuard:**
```bash
ssh root@15.204.11.19 "
systemctl start wg-quick@wg0
systemctl enable wg-quick@wg0
wg show
"
```

### **3. Deploy PhazeVPN:**
```bash
ssh root@15.204.11.19 "
# Copy binary
cp /root/phazevpn-backup-*/phazevpn/phazevpn-protocol-go/phazevpn-server /usr/local/bin/

# Create service
cat > /etc/systemd/system/phazevpn-server.service <<EOF
[Unit]
Description=PhazeVPN Protocol Server
After=network.target

[Service]
Type=simple
User=root
ExecStart=/usr/local/bin/phazevpn-server --host 0.0.0.0 --port 51821 --network 10.9.0.0/24
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Start service
systemctl daemon-reload
systemctl start phazevpn-server
systemctl enable phazevpn-server
"
```

### **4. Verify All Protocols:**
```bash
ssh root@15.204.11.19 "
echo '=== LISTENING PORTS ==='
netstat -tulnp | grep -E '(51820|1194|51821)'

echo ''
echo '=== SERVICE STATUS ==='
systemctl status wg-quick@wg0 --no-pager | head -5
systemctl status openvpn@server --no-pager | head -5
systemctl status phazevpn-server --no-pager | head -5
"
```

---

## ✅ **FINAL CONFIGURATION**

### **Summary:**
```
Protocol    | Port  | Network      | Status
------------|-------|--------------|--------
OpenVPN     | 1194  | 10.8.0.0/24  | ✅ Running
WireGuard   | 51820 | 10.7.0.0/24  | ⚠️ Ready
PhazeVPN    | 51821 | 10.9.0.0/24  | ❌ Needs deploy
```

### **All 3 Can Run Simultaneously:**
```
✅ Different ports (no conflicts)
✅ Different networks (no IP conflicts)
✅ Different protocols (no interference)
✅ Users can choose preferred protocol
✅ Can switch without disconnecting others
```

---

**Ready to deploy all 3 protocols with proper port separation?**
