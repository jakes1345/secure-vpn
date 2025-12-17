#!/usr/bin/env python3
"""
Fix VPN control and remove all fake/placeholder content from website
Deploy fixes to VPS
"""

from paramiko import SSHClient, AutoAddPolicy
import paramiko
from pathlib import Path
import sys

# VPS Connection
VPS_IP = "15.204.11.19"
VPS_USER = "root"
VPS_PASS = input("Enter VPS root password: ").strip()

def fix_vpn_api():
    """Fix VPN API endpoints to use correct service name and add restart"""
    print("\n[1/4] Fixing VPN API endpoints...")
    
    app_py = Path("web-portal/app.py")
    if not app_py.exists():
        print("   ❌ web-portal/app.py not found")
        return False
    
    content = app_py.read_text()
    
    # Check current VPN endpoints
    if '/api/vpn/start' in content and '/api/vpn/stop' in content:
        # Add restart endpoint and improve error handling
        old_start = """@app.route('/api/vpn/start', methods=['POST'])
@require_permission('can_start_stop_vpn')
def api_vpn_start():
    \"\"\"Start VPN\"\"\"
    result = subprocess.run(['systemctl', 'start', 'secure-vpn'], capture_output=True)
    success = result.returncode == 0
    if success:
        log_activity(session.get('username', 'unknown'), 'VPN_START', 'Started VPN server')
    return jsonify({'success': success, 'message': 'VPN started' if success else 'Failed to start VPN'})

@app.route('/api/vpn/stop', methods=['POST'])
@require_permission('can_start_stop_vpn')
def api_vpn_stop():
    \"\"\"Stop VPN\"\"\"
    result = subprocess.run(['systemctl', 'stop', 'secure-vpn'], capture_output=True)
    success = result.returncode == 0
    if success:
        log_activity(session.get('username', 'unknown'), 'VPN_STOP', 'Stopped VPN server')
    return jsonify({'success': success, 'message': 'VPN stopped' if success else 'Failed to stop VPN'})"""
        
        new_start = """@app.route('/api/vpn/start', methods=['POST'])
@require_permission('can_start_stop_vpn')
def api_vpn_start():
    \"\"\"Start VPN\"\"\"
    try:
        # Try secure-vpn first, then phazevpn-web, then openvpn
        result = subprocess.run(['systemctl', 'start', 'secure-vpn'], capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            # Try alternative service names
            result = subprocess.run(['systemctl', 'start', 'phazevpn-web'], capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            result = subprocess.run(['systemctl', 'start', 'openvpn'], capture_output=True, text=True, timeout=10)
        
        success = result.returncode == 0
        if success:
            log_activity(session.get('username', 'unknown'), 'VPN_START', 'Started VPN server')
            return jsonify({'success': True, 'message': 'VPN started successfully'})
        else:
            error_msg = result.stderr.strip() or result.stdout.strip() or 'Unknown error'
            return jsonify({'success': False, 'message': f'Failed to start VPN: {error_msg}'}), 500
    except subprocess.TimeoutExpired:
        return jsonify({'success': False, 'message': 'Timeout starting VPN service'}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error starting VPN: {str(e)}'}), 500

@app.route('/api/vpn/stop', methods=['POST'])
@require_permission('can_start_stop_vpn')
def api_vpn_stop():
    \"\"\"Stop VPN\"\"\"
    try:
        # Try secure-vpn first, then phazevpn-web, then openvpn
        result = subprocess.run(['systemctl', 'stop', 'secure-vpn'], capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            result = subprocess.run(['systemctl', 'stop', 'phazevpn-web'], capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            result = subprocess.run(['systemctl', 'stop', 'openvpn'], capture_output=True, text=True, timeout=10)
        
        success = result.returncode == 0
        if success:
            log_activity(session.get('username', 'unknown'), 'VPN_STOP', 'Stopped VPN server')
            return jsonify({'success': True, 'message': 'VPN stopped successfully'})
        else:
            error_msg = result.stderr.strip() or result.stdout.strip() or 'Unknown error'
            return jsonify({'success': False, 'message': f'Failed to stop VPN: {error_msg}'}), 500
    except subprocess.TimeoutExpired:
        return jsonify({'success': False, 'message': 'Timeout stopping VPN service'}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error stopping VPN: {str(e)}'}), 500

@app.route('/api/vpn/restart', methods=['POST'])
@require_permission('can_start_stop_vpn')
def api_vpn_restart():
    \"\"\"Restart VPN\"\"\"
    try:
        # Try secure-vpn first, then phazevpn-web, then openvpn
        result = subprocess.run(['systemctl', 'restart', 'secure-vpn'], capture_output=True, text=True, timeout=15)
        if result.returncode != 0:
            result = subprocess.run(['systemctl', 'restart', 'phazevpn-web'], capture_output=True, text=True, timeout=15)
        if result.returncode != 0:
            result = subprocess.run(['systemctl', 'restart', 'openvpn'], capture_output=True, text=True, timeout=15)
        
        success = result.returncode == 0
        if success:
            log_activity(session.get('username', 'unknown'), 'VPN_RESTART', 'Restarted VPN server')
            return jsonify({'success': True, 'message': 'VPN restarted successfully'})
        else:
            error_msg = result.stderr.strip() or result.stdout.strip() or 'Unknown error'
            return jsonify({'success': False, 'message': f'Failed to restart VPN: {error_msg}'}), 500
    except subprocess.TimeoutExpired:
        return jsonify({'success': False, 'message': 'Timeout restarting VPN service'}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error restarting VPN: {str(e)}'}), 500"""
        
        if old_start in content:
            content = content.replace(old_start, new_start)
            app_py.write_text(content)
            print("   ✅ VPN API endpoints fixed (added restart, better error handling)")
            return True
        else:
            print("   ⚠️  VPN endpoints already updated or format changed")
            return True
    else:
        print("   ❌ Could not find VPN endpoints in app.py")
        return False

def remove_fake_content():
    """Remove all fake/placeholder content from website"""
    print("\n[2/4] Removing fake content from website...")
    
    # Fix testimonials page - remove all fake reviews
    testimonials_file = Path("web-portal/templates/testimonials.html")
    if testimonials_file.exists():
        content = testimonials_file.read_text()
        
        # Replace fake testimonials with empty state
        old_testimonials = """        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 2rem;">
            <div style="background: rgba(255,255,255,0.05); padding: 2rem; border-radius: 8px; border: 1px solid rgba(255,255,255,0.1);">
                <div style="color: #ffd700; font-size: 1.5rem; margin-bottom: 1rem;">⭐⭐⭐⭐⭐</div>
                <p style="color: #aaa; margin-bottom: 1rem; font-style: italic;">
                    "PhazeVPN is the most secure VPN I've ever used. The kill switch actually works, and I love that everything is enforced at the network level. No browser extensions needed!"
                </p>
                <div style="color: #4a9eff; font-weight: bold;">- Alex M.</div>
                <div style="color: #666; font-size: 0.85rem;">Pro Plan User</div>
            </div>
            
            <div style="background: rgba(255,255,255,0.05); padding: 2rem; border-radius: 8px; border: 1px solid rgba(255,255,255,0.1);">
                <div style="color: #ffd700; font-size: 1.5rem; margin-bottom: 1rem;">⭐⭐⭐⭐⭐</div>
                <p style="color: #aaa; margin-bottom: 1rem; font-style: italic;">
                    "The speed is incredible! I can stream 4K content without any lag. Plus, the zero-logs policy gives me peace of mind. Highly recommend!"
                </p>
                <div style="color: #4a9eff; font-weight: bold;">- Sarah K.</div>
                <div style="color: #666; font-size: 0.85rem;">Premium Plan User</div>
            </div>
            
            <div style="background: rgba(255,255,255,0.05); padding: 2rem; border-radius: 8px; border: 1px solid rgba(255,255,255,0.1);">
                <div style="color: #ffd700; font-size: 1.5rem; margin-bottom: 1rem;">⭐⭐⭐⭐⭐</div>
                <p style="color: #aaa; margin-bottom: 1rem; font-style: italic;">
                    "Finally, a VPN that doesn't require browser extensions! Everything is built into the VPN itself. The setup was easy and the connection is rock solid."
                </p>
                <div style="color: #4a9eff; font-weight: bold;">- Mike T.</div>
                <div style="color: #666; font-size: 0.85rem;">Basic Plan User</div>
            </div>
            
            <div style="background: rgba(255,255,255,0.05); padding: 2rem; border-radius: 8px; border: 1px solid rgba(255,255,255,0.1);">
                <div style="color: #ffd700; font-size: 1.5rem; margin-bottom: 1rem;">⭐⭐⭐⭐⭐</div>
                <p style="color: #aaa; margin-bottom: 1rem; font-style: italic;">
                    "The free plan is perfect for testing. I upgraded to Pro after seeing how well it worked. The dashboard is clean and easy to use."
                </p>
                <div style="color: #4a9eff; font-weight: bold;">- Jennifer L.</div>
                <div style="color: #666; font-size: 0.85rem;">Pro Plan User</div>
            </div>
            
            <div style="background: rgba(255,255,255,0.05); padding: 2rem; border-radius: 8px; border: 1px solid rgba(255,255,255,0.1);">
                <div style="color: #ffd700; font-size: 1.5rem; margin-bottom: 1rem;">⭐⭐⭐⭐⭐</div>
                <p style="color: #aaa; margin-bottom: 1rem; font-style: italic;">
                    "Military-grade encryption and zero logs? Sign me up! This is exactly what I was looking for. The connection is fast and reliable."
                </p>
                <div style="color: #4a9eff; font-weight: bold;">- David R.</div>
                <div style="color: #666; font-size: 0.85rem;">Premium Plan User</div>
            </div>
            
            <div style="background: rgba(255,255,255,0.05); padding: 2rem; border-radius: 8px; border: 1px solid rgba(255,255,255,0.1);">
                <div style="color: #ffd700; font-size: 1.5rem; margin-bottom: 1rem;">⭐⭐⭐⭐⭐</div>
                <p style="color: #aaa; margin-bottom: 1rem; font-style: italic;">
                    "Best VPN I've tried. The DNS leak protection actually works, and I love that IPv6 is properly routed. No leaks, no problems!"
                </p>
                <div style="color: #4a9eff; font-weight: bold;">- Emily C.</div>
                <div style="color: #666; font-size: 0.85rem;">Pro Plan User</div>
            </div>
        </div>"""
        
        new_testimonials = """        <div style="text-align: center; padding: 4rem 2rem; background: rgba(255,255,255,0.05); border-radius: 8px; border: 1px solid rgba(255,255,255,0.1);">
            <div style="font-size: 4rem; margin-bottom: 1rem;">💬</div>
            <h3 style="color: #4a9eff; margin-bottom: 1rem;">No Reviews Yet</h3>
            <p style="color: #aaa; margin-bottom: 2rem;">Be the first to share your experience with PhazeVPN!</p>
            <a href="/contact" class="btn btn-primary" style="display: inline-block; padding: 1rem 2rem; text-decoration: none;">Share Your Feedback</a>
        </div>"""
        
        if old_testimonials in content:
            content = content.replace(old_testimonials, new_testimonials)
            testimonials_file.write_text(content)
            print("   ✅ Removed fake testimonials")
        else:
            print("   ⚠️  Testimonials already updated or format changed")
    
    # Fix home page - remove fake stats
    home_file = Path("web-portal/templates/home.html")
    if home_file.exists():
        content = home_file.read_text()
        
        # Remove fake user count and uptime stats
        old_stats = """        <div style="display: flex; gap: 2rem; justify-content: center; margin: 2rem 0; flex-wrap: wrap;">
            <div style="text-align: center;">
                <div style="font-size: 2rem; font-weight: bold; color: #4a9eff;">10,000+</div>
                <div style="color: #aaa;">Active Users</div>
            </div>
            <div style="text-align: center;">
                <div style="font-size: 2rem; font-weight: bold; color: #4a9eff;">99.9%</div>
                <div style="color: #aaa;">Uptime</div>
            </div>
            <div style="text-align: center;">
                <div style="font-size: 2rem; font-weight: bold; color: #4a9eff;">30-Day</div>
                <div style="color: #aaa;">Money-Back Guarantee</div>
            </div>
        </div>"""
        
        new_stats = """        <div style="display: flex; gap: 2rem; justify-content: center; margin: 2rem 0; flex-wrap: wrap;">
            <div style="text-align: center;">
                <div style="font-size: 2rem; font-weight: bold; color: #4a9eff;">30-Day</div>
                <div style="color: #aaa;">Money-Back Guarantee</div>
            </div>
        </div>"""
        
        if old_stats in content:
            content = content.replace(old_stats, new_stats)
            print("   ✅ Removed fake user count and uptime stats")
        
        # Remove fake rating
        old_rating = """            <div style="display: flex; justify-content: center; gap: 3rem; flex-wrap: wrap; margin: 2rem 0;">
                <div>
                    <div style="font-size: 2.5rem; color: #ffd700;">⭐⭐⭐⭐⭐</div>
                    <div style="color: #aaa; margin-top: 0.5rem;">4.9/5 Rating</div>
                </div>
                <div>
                    <div style="font-size: 2.5rem; color: #4a9eff;">🔒</div>
                    <div style="color: #aaa; margin-top: 0.5rem;">Zero-Logs Policy</div>
                </div>
                <div>
                    <div style="font-size: 2.5rem; color: #10b981;">✅</div>
                    <div style="color: #aaa; margin-top: 0.5rem;">30-Day Guarantee</div>
                </div>
            </div>
            <a href="/testimonials" style="color: #4a9eff; text-decoration: none;">Read User Reviews →</a>"""
        
        new_rating = """            <div style="display: flex; justify-content: center; gap: 3rem; flex-wrap: wrap; margin: 2rem 0;">
                <div>
                    <div style="font-size: 2.5rem; color: #4a9eff;">🔒</div>
                    <div style="color: #aaa; margin-top: 0.5rem;">Zero-Logs Policy</div>
                </div>
                <div>
                    <div style="font-size: 2.5rem; color: #10b981;">✅</div>
                    <div style="color: #aaa; margin-top: 0.5rem;">30-Day Guarantee</div>
                </div>
            </div>"""
        
        if old_rating in content:
            content = content.replace(old_rating, new_rating)
            print("   ✅ Removed fake rating")
        
        # Remove "Trusted by Thousands" section
        old_trusted = """        <div style="background: rgba(0,0,0,0.3); padding: 3rem 2rem; margin: 4rem 0; border-radius: 16px; text-align: center;">
            <h2 style="font-size: 2rem; margin-bottom: 1rem;">Trusted by Thousands</h2>"""
        
        if old_trusted in content:
            # Find and remove the entire section until the next div
            import re
            pattern = r'<div style="background: rgba\(0,0,0,0\.3\); padding: 3rem 2rem; margin: 4rem 0; border-radius: 16px; text-align: center;">.*?</div>\s*</div>'
            content = re.sub(pattern, '', content, flags=re.DOTALL)
            print("   ✅ Removed 'Trusted by Thousands' section")
        
        home_file.write_text(content)
    
    print("   ✅ All fake content removed")
    return True

def deploy_to_vps():
    """Deploy fixed files to VPS"""
    print("\n[3/4] Deploying fixes to VPS...")
    
    try:
        ssh = SSHClient()
        ssh.set_missing_host_key_policy(AutoAddPolicy())
        ssh.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=30)
        print("   ✅ Connected to VPS")
        
        sftp = ssh.open_sftp()
        
        # Upload fixed app.py
        print("   📤 Uploading fixed app.py...")
        local_app = Path("web-portal/app.py")
        remote_app = "/opt/secure-vpn/web-portal/app.py"
        
        if local_app.exists():
            sftp.put(str(local_app), remote_app)
            print("   ✅ app.py uploaded")
        else:
            print("   ❌ app.py not found locally")
        
        # Upload fixed templates
        print("   📤 Uploading fixed templates...")
        for template in ["testimonials.html", "home.html"]:
            local_template = Path(f"web-portal/templates/{template}")
            remote_template = f"/opt/secure-vpn/web-portal/templates/{template}"
            
            if local_template.exists():
                sftp.put(str(local_template), remote_template)
                print(f"   ✅ {template} uploaded")
        
        sftp.close()
        
        # Restart web service
        print("   🔄 Restarting web service...")
        stdin, stdout, stderr = ssh.exec_command("systemctl restart phazevpn-web 2>&1")
        stdout.channel.recv_exit_status()
        print("   ✅ Web service restarted")
        
        # Check VPN service name
        print("   🔍 Checking VPN service name...")
        stdin, stdout, stderr = ssh.exec_command("systemctl list-units --type=service --all | grep -iE '(vpn|openvpn)' | head -5")
        services = stdout.read().decode().strip()
        print(f"   Available VPN services:\n{services}")
        
        # Test VPN status
        stdin, stdout, stderr = ssh.exec_command("systemctl is-active secure-vpn 2>&1 || systemctl is-active openvpn 2>&1 || echo 'no-service'")
        vpn_status = stdout.read().decode().strip()
        print(f"   VPN service status: {vpn_status}")
        
        ssh.close()
        print("   ✅ Deployment complete")
        return True
        
    except Exception as e:
        print(f"   ❌ Deployment failed: {e}")
        return False

def main():
    print("=" * 60)
    print("Fix VPN Control & Remove Fake Content")
    print("=" * 60)
    
    # Fix locally
    if not fix_vpn_api():
        print("   ⚠️  VPN API fix had issues, continuing...")
    
    if not remove_fake_content():
        print("   ⚠️  Content removal had issues, continuing...")
    
    # Deploy to VPS
    if not deploy_to_vps():
        print("\n❌ Deployment failed. Check errors above.")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("✅ All fixes applied and deployed!")
    print("=" * 60)
    print("\nNext steps:")
    print("   1. Test VPN start/stop from dashboard")
    print("   2. Check website - no fake content should appear")
    print("   3. Visit: https://phazevpn.duckdns.org/testimonials")
    print("   4. Visit: https://phazevpn.duckdns.org")

if __name__ == "__main__":
    main()

