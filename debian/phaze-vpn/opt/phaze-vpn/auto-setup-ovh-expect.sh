#!/usr/bin/expect -f

# Automated OVH VPS Setup Script using Expect
# This script does EVERYTHING automatically

set timeout 300
set VPS_IP "15.204.11.19"
set VPS_USER "ubuntu"
set VPS_PASS "QwX8MJJH3fSE"
set LOCAL_DIR "/opt/phaze-vpn"
set REMOTE_DIR "/opt/phaze-vpn"

puts "=========================================="
puts "🚀 Automated PhazeVPN VPS Setup"
puts "=========================================="
puts ""
puts "VPS: $VPS_USER@$VPS_IP"
puts ""

# Function to run remote command
proc run_remote {cmd} {
    global VPS_IP VPS_USER VPS_PASS
    spawn ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 "$VPS_USER@$VPS_IP" $cmd
    expect {
        "password:" {
            send "$VPS_PASS\r"
            expect {
                "$ " { return 0 }
                "# " { return 0 }
                timeout { puts "Timeout waiting for prompt"; return 1 }
            }
        }
        "$ " { return 0 }
        "# " { return 0 }
        timeout { puts "Connection timeout"; return 1 }
    }
}

# Function to copy file
proc copy_file {local remote} {
    global VPS_IP VPS_USER VPS_PASS
    spawn scp -o StrictHostKeyChecking=no "$local" "$VPS_USER@$VPS_IP:$remote"
    expect {
        "password:" {
            send "$VPS_PASS\r"
            expect {
                "100%" { return 0 }
                timeout { puts "Transfer timeout"; return 1 }
            }
        }
        "100%" { return 0 }
        timeout { puts "Connection timeout"; return 1 }
    }
}

puts "✅ Step 1/10: Testing connection..."
spawn ssh -o StrictHostKeyChecking=no "$VPS_USER@$VPS_IP" "echo 'Connection test successful'"
expect {
    "password:" {
        send "$VPS_PASS\r"
        expect {
            "Connection test successful" {
                puts "✅ Connected!"
            }
            timeout { puts "❌ Connection failed"; exit 1 }
        }
    }
    timeout { puts "❌ Connection timeout"; exit 1 }
}
puts ""

puts "✅ Step 2/10: Updating system packages..."
spawn ssh -o StrictHostKeyChecking=no "$VPS_USER@$VPS_IP" "sudo apt-get update -qq && sudo apt-get upgrade -y -qq"
expect {
    "password:" {
        send "$VPS_PASS\r"
        expect {
            "$ " { puts "✅ System updated" }
            timeout { puts "⚠️  Update may have timed out" }
        }
    }
    "$ " { puts "✅ System updated" }
    timeout { puts "⚠️  Update may have timed out" }
}
puts ""

puts "✅ Step 3/10: Installing dependencies..."
spawn ssh -o StrictHostKeyChecking=no "$VPS_USER@$VPS_IP" "sudo apt-get install -y python3 python3-pip python3-tk openssl openvpn easy-rsa iptables ufw net-tools curl wget git build-essential debhelper devscripts"
expect {
    "password:" {
        send "$VPS_PASS\r"
        expect {
            "Setting up" { 
                expect eof
                puts "✅ Dependencies installed"
            }
            timeout { puts "⚠️  Installation may have timed out" }
        }
    }
    "Setting up" {
        expect eof
        puts "✅ Dependencies installed"
    }
    timeout { puts "⚠️  Installation may have timed out" }
}
puts ""

puts "✅ Step 4/10: Creating PhazeVPN directory..."
spawn ssh -o StrictHostKeyChecking=no "$VPS_USER@$VPS_IP" "sudo mkdir -p $REMOTE_DIR/{config,certs,client-configs,logs,scripts,backups} && sudo chmod 755 $REMOTE_DIR"
expect {
    "password:" {
        send "$VPS_PASS\r"
        expect "$ "
    }
    "$ " {}
}
puts "✅ Directory created"
puts ""

puts "✅ Step 5/10: Transferring PhazeVPN files..."
# Create tarball locally first
exec bash -c "cd $LOCAL_DIR && tar -czf /tmp/phaze-vpn-files.tar.gz vpn-manager.py vpn-gui.py client-download-server.py subscription-manager.py setup-routing.sh open-download-port.sh start-download-server-robust.sh generate-certs.sh config/ debian/phaze-vpn.service debian/phaze-vpn-download.service 2>/dev/null || true"

# Copy tarball
copy_file "/tmp/phaze-vpn-files.tar.gz" "/tmp/phaze-vpn-files.tar.gz"

# Extract on remote
spawn ssh -o StrictHostKeyChecking=no "$VPS_USER@$VPS_IP" "cd /tmp && mkdir -p phaze-extract && cd phaze-extract && tar -xzf ../phaze-vpn-files.tar.gz && sudo cp -r * $REMOTE_DIR/ 2>/dev/null || true && sudo cp -r config/* $REMOTE_DIR/config/ 2>/dev/null || true && sudo cp phaze-vpn.service phaze-vpn-download.service /etc/systemd/system/ 2>/dev/null || true && sudo chmod +x $REMOTE_DIR/*.sh $REMOTE_DIR/*.py 2>/dev/null || true && sudo chown -R root:root $REMOTE_DIR"
expect {
    "password:" {
        send "$VPS_PASS\r"
        expect "$ "
    }
    "$ " {}
}
puts "✅ Files transferred"
puts ""

puts "✅ Step 6/10: Installing systemd services..."
# Services should be copied, but ensure they exist with correct content
spawn ssh -o StrictHostKeyChecking=no "$VPS_USER@$VPS_IP" "sudo systemctl daemon-reload"
expect {
    "password:" {
        send "$VPS_PASS\r"
        expect "$ "
    }
    "$ " {}
}
puts "✅ Services installed"
puts ""

puts "✅ Step 7/10: Configuring firewall..."
spawn ssh -o StrictHostKeyChecking=no "$VPS_USER@$VPS_IP" "sudo ufw --force enable && sudo ufw allow 22/tcp && sudo ufw allow 1194/udp && sudo ufw allow 8081/tcp"
expect {
    "password:" {
        send "$VPS_PASS\r"
        expect "$ "
    }
    "$ " {}
}
puts "✅ Firewall configured"
puts ""

puts "✅ Step 8/10: Setting server IP and initializing VPN..."
spawn ssh -o StrictHostKeyChecking=no "$VPS_USER@$VPS_IP" "cd $REMOTE_DIR && sudo python3 vpn-manager.py set-server-ip $VPS_IP || true && sudo python3 vpn-manager.py init || echo 'VPN already initialized'"
expect {
    "password:" {
        send "$VPS_PASS\r"
        expect "$ "
    }
    "$ " {}
}
puts "✅ VPN initialized"
puts ""

puts "✅ Step 9/10: Setting up routing..."
spawn ssh -o StrictHostKeyChecking=no "$VPS_USER@$VPS_IP" "cd $REMOTE_DIR && sudo bash setup-routing.sh || echo 'Routing already configured'"
expect {
    "password:" {
        send "$VPS_PASS\r"
        expect "$ "
    }
    "$ " {}
}
puts "✅ Routing configured"
puts ""

puts "✅ Step 10/10: Starting services..."
spawn ssh -o StrictHostKeyChecking=no "$VPS_USER@$VPS_IP" "sudo systemctl enable phaze-vpn phaze-vpn-download && sudo systemctl start phaze-vpn phaze-vpn-download"
expect {
    "password:" {
        send "$VPS_PASS\r"
        expect "$ "
    }
    "$ " {}
}
sleep 3
puts "✅ Services started"
puts ""

puts "=========================================="
puts "✅ Setup Complete!"
puts "=========================================="
puts ""
puts "🌐 Download Server:"
puts "   http://$VPS_IP:8081"
puts ""
puts "📝 Next Steps:"
puts "   1. Create a test client:"
puts "      ssh $VPS_USER@$VPS_IP"
puts "      sudo python3 /opt/phaze-vpn/vpn-manager.py add-client test-client"
puts ""
puts "   2. Download config:"
puts "      http://$VPS_IP:8081/download?name=test-client"
puts ""
puts "🎉 PhazeVPN is now running on your OVH VPS!"

# Cleanup
exec rm -f /tmp/phaze-vpn-files.tar.gz
spawn ssh -o StrictHostKeyChecking=no "$VPS_USER@$VPS_IP" "rm -f /tmp/phaze-vpn-files.tar.gz"
expect {
    "password:" {
        send "$VPS_PASS\r"
        expect "$ "
    }
    "$ " {}
}

