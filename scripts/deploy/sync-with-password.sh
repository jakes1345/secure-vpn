#!/usr/bin/expect -f
# Sync script with password automation

set timeout 30
set VPS_IP "15.204.11.19"
set VPS_USER "root"
set VPS_PASS "Jakes1328!@"
set VPS_PATH "/opt/secure-vpn"
set LOCAL_PATH "/opt/phaze-vpn"

puts "=========================================="
puts "🔄 SYNCING LOCAL CHANGES TO VPS"
puts "=========================================="
puts ""

# Function to run scp command
proc sync_file {local_file remote_file} {
    global VPS_IP VPS_USER VPS_PASS
    
    puts "Syncing $local_file..."
    spawn scp $local_file ${VPS_USER}@${VPS_IP}:$remote_file
    expect {
        "password:" {
            send "$VPS_PASS\r"
            expect {
                "100%" {
                    puts "   ✓ Success"
                    expect eof
                }
                timeout {
                    puts "   ✗ Timeout"
                    exit 1
                }
            }
        }
        "Permission denied" {
            puts "   ✗ Permission denied"
            exit 1
        }
        timeout {
            puts "   ✗ Connection timeout"
            exit 1
        }
    }
}

# Sync files
sync_file "$LOCAL_PATH/web-portal/app.py" "$VPS_PATH/web-portal/app.py"
sync_file "$LOCAL_PATH/web-portal/requirements.txt" "$VPS_PATH/web-portal/requirements.txt"
sync_file "$LOCAL_PATH/web-portal/templates/base.html" "$VPS_PATH/web-portal/templates/base.html"

puts ""
puts "=========================================="
puts "✅ SYNC COMPLETE!"
puts "=========================================="
puts ""
puts "Next: SSH in and run:"
puts "  cd $VPS_PATH/web-portal"
puts "  pip3 install -r requirements.txt"
puts "  sudo systemctl restart secure-vpn-portal"
puts ""

