#!/usr/bin/expect -f
# Sync ALL Security Updates to VPS with Password Automation

set timeout 60
set VPS_IP "15.204.11.19"
set VPS_USER "root"
set VPS_PASS "Jakes1328!@"
set VPS_PATH "/opt/secure-vpn"
set LOCAL_PATH "/opt/phaze-vpn"

puts "=========================================="
puts "🔄 SYNCING SECURITY UPDATES TO VPS"
puts "=========================================="
puts ""
puts "VPS: ${VPS_USER}@${VPS_IP}"
puts "Remote Path: ${VPS_PATH}"
puts "Local Path: ${LOCAL_PATH}"
puts ""

# Function to run scp command
proc sync_file {local_file remote_file} {
    global VPS_IP VPS_USER VPS_PASS
    
    puts "Syncing [file tail $local_file]..."
    spawn scp $local_file ${VPS_USER}@${VPS_IP}:$remote_file
    expect {
        "password:" {
            send "$VPS_PASS\r"
            expect {
                "100%" {
                    puts "   ✓ Success"
                    expect eof
                }
                "Permission denied" {
                    puts "   ✗ Permission denied"
                    exit 1
                }
                timeout {
                    puts "   ✗ Timeout"
                    exit 1
                }
            }
        }
        "yes/no" {
            send "yes\r"
            exp_continue
        }
        "Permission denied" {
            puts "   ✗ Permission denied"
            exit 1
        }
        timeout {
            puts "   ✗ Connection timeout"
            exit 1
        }
        eof {
            puts "   ✓ Success"
        }
    }
}

# Function to run ssh command
proc run_ssh {command} {
    global VPS_IP VPS_USER VPS_PASS
    
    spawn ssh ${VPS_USER}@${VPS_IP} $command
    expect {
        "password:" {
            send "$VPS_PASS\r"
            expect {
                eof {
                    # Command completed
                }
                timeout {
                    puts "   ⚠️  Timeout"
                }
            }
        }
        "yes/no" {
            send "yes\r"
            exp_continue
        }
        eof {
            # Already connected or command completed
        }
    }
}

puts "📋 Security files to sync:"
puts "  ✓ config/server.conf"
puts "  ✓ scripts/up-ultimate-security.sh"
puts "  ✓ scripts/down-ultimate-security.sh"
puts "  ✓ scripts/setup-ddos-protection.sh"
puts "  ✓ scripts/enhance-privacy.sh"
puts "  ✓ scripts/setup-vpn-ipv6.sh"
puts "  ✓ vpn-manager.py"
puts ""

# Create backup directory
puts "📦 Creating backup on VPS..."
run_ssh "mkdir -p ${VPS_PATH}/backups/\[date +%Y%m%d-%H%M%S\]"

puts ""
puts "🚀 Starting sync..."
puts ""

# Sync server config
puts "[1/7] Syncing config/server.conf..."
sync_file "${LOCAL_PATH}/config/server.conf" "${VPS_PATH}/config/server.conf"

# Sync security scripts
puts "[2/7] Syncing scripts/up-ultimate-security.sh..."
sync_file "${LOCAL_PATH}/scripts/up-ultimate-security.sh" "${VPS_PATH}/scripts/up-ultimate-security.sh"
run_ssh "chmod +x ${VPS_PATH}/scripts/up-ultimate-security.sh"

puts "[3/7] Syncing scripts/down-ultimate-security.sh..."
sync_file "${LOCAL_PATH}/scripts/down-ultimate-security.sh" "${VPS_PATH}/scripts/down-ultimate-security.sh"
run_ssh "chmod +x ${VPS_PATH}/scripts/down-ultimate-security.sh"

puts "[4/7] Syncing scripts/setup-ddos-protection.sh..."
sync_file "${LOCAL_PATH}/scripts/setup-ddos-protection.sh" "${VPS_PATH}/scripts/setup-ddos-protection.sh"
run_ssh "chmod +x ${VPS_PATH}/scripts/setup-ddos-protection.sh"

puts "[5/7] Syncing scripts/enhance-privacy.sh..."
sync_file "${LOCAL_PATH}/scripts/enhance-privacy.sh" "${VPS_PATH}/scripts/enhance-privacy.sh"
run_ssh "chmod +x ${VPS_PATH}/scripts/enhance-privacy.sh"

puts "[6/7] Syncing scripts/setup-vpn-ipv6.sh..."
sync_file "${LOCAL_PATH}/scripts/setup-vpn-ipv6.sh" "${VPS_PATH}/scripts/setup-vpn-ipv6.sh"
run_ssh "chmod +x ${VPS_PATH}/scripts/setup-vpn-ipv6.sh"

puts "[7/7] Syncing vpn-manager.py..."
sync_file "${LOCAL_PATH}/vpn-manager.py" "${VPS_PATH}/vpn-manager.py"
run_ssh "chmod +x ${VPS_PATH}/vpn-manager.py"

puts ""
puts "=========================================="
puts "✅ SYNC COMPLETE!"
puts "=========================================="
puts ""
puts "📝 Next steps on VPS:"
puts ""
puts "1. SSH into VPS:"
puts "   ssh ${VPS_USER}@${VPS_IP}"
puts "   Password: ${VPS_PASS}"
puts ""
puts "2. Setup DDoS protection:"
puts "   cd ${VPS_PATH}"
puts "   sudo ./scripts/setup-ddos-protection.sh"
puts ""
puts "3. Setup privacy enhancements:"
puts "   sudo ./scripts/enhance-privacy.sh"
puts ""
puts "4. Restart OpenVPN:"
puts "   sudo systemctl restart openvpn@server"
puts "   # OR: sudo systemctl restart secure-vpn"
puts ""
puts "5. Test VPN connection and verify security features"
puts ""
puts "=========================================="

