#!/usr/bin/env python3
"""
PhazeVPN Protocol - Client Management Tool
Easy command-line tool to manage clients
"""

import sys
import argparse
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from client_manager import ClientManager

def main():
    parser = argparse.ArgumentParser(description='PhazeVPN Protocol Client Manager')
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Create user command
    create_parser = subparsers.add_parser('create', help='Create new user')
    create_parser.add_argument('username', help='Username')
    create_parser.add_argument('--password', help='Password (auto-generated if not provided)')
    create_parser.add_argument('--mode', choices=['normal', 'semi_ghost', 'full_ghost'], 
                              default='normal', help='VPN mode')
    create_parser.add_argument('--server-ip', default='15.204.11.19', help='Server IP')
    
    # List users command
    list_parser = subparsers.add_parser('list', help='List all users')
    
    # Delete user command
    delete_parser = subparsers.add_parser('delete', help='Delete user')
    delete_parser.add_argument('username', help='Username to delete')
    
    # Reset password command
    reset_parser = subparsers.add_parser('reset-password', help='Reset user password')
    reset_parser.add_argument('username', help='Username')
    
    # Update mode command
    mode_parser = subparsers.add_parser('set-mode', help='Set user VPN mode')
    mode_parser.add_argument('username', help='Username')
    mode_parser.add_argument('mode', choices=['normal', 'semi_ghost', 'full_ghost'], help='VPN mode')
    
    # Show user info command
    info_parser = subparsers.add_parser('info', help='Show user information')
    info_parser.add_argument('username', help='Username')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    manager = ClientManager()
    
    try:
        if args.command == 'create':
            print("=" * 70)
            print("👤 Creating PhazeVPN Client")
            print("=" * 70)
            print(f"Username: {args.username}")
            print(f"Mode: {args.mode}")
            print("")
            
            user_info = manager.create_user(args.username, args.password, args.mode)
            
            print("✅ User created successfully!")
            print("")
            print("📋 User Details:")
            print(f"   Username: {user_info['username']}")
            print(f"   Password: {user_info['password']}")
            print(f"   Mode: {user_info['mode']}")
            print(f"   Config: {user_info['config_file']}")
            print("")
            print("⚠️  IMPORTANT: Save this password! It won't be shown again.")
            print("   Use 'reset-password' command to change it.")
            print("")
        
        elif args.command == 'list':
            users = manager.list_users()
            if not users:
                print("No users found.")
                return
            
            print("=" * 70)
            print("👥 PhazeVPN Users")
            print("=" * 70)
            print("")
            
            for user in users:
                status = "✅ Active" if user['active'] else "❌ Inactive"
                print(f"👤 {user['username']}")
                print(f"   Mode: {user['mode']}")
                print(f"   Status: {status}")
                print(f"   Created: {user.get('created', 'Unknown')}")
                print(f"   Connections: {user.get('total_connections', 0)}")
                print("")
        
        elif args.command == 'delete':
            if manager.delete_user(args.username):
                print(f"✅ User '{args.username}' deleted")
            else:
                print(f"❌ User '{args.username}' not found")
        
        elif args.command == 'reset-password':
            new_password = manager.reset_password(args.username)
            print("=" * 70)
            print(f"🔑 Password Reset for: {args.username}")
            print("=" * 70)
            print(f"New Password: {new_password}")
            print("")
            print("⚠️  IMPORTANT: Save this password! It won't be shown again.")
            print("✅ Client config updated with new password")
        
        elif args.command == 'set-mode':
            manager.update_user_mode(args.username, args.mode)
            print(f"✅ User '{args.username}' mode set to: {args.mode}")
            print("⚠️  Note: Regenerate client config to apply new mode")
        
        elif args.command == 'info':
            user_info = manager.get_user_info(args.username)
            if not user_info:
                print(f"❌ User '{args.username}' not found")
                return
            
            print("=" * 70)
            print(f"👤 User Information: {args.username}")
            print("=" * 70)
            print(f"Mode: {user_info.get('mode', 'normal')}")
            print(f"Status: {'✅ Active' if user_info.get('active', True) else '❌ Inactive'}")
            print(f"Created: {user_info.get('created', 'Unknown')}")
            print(f"Total Connections: {user_info.get('total_connections', 0)}")
            print(f"Last Connected: {user_info.get('last_connected', 'Never')}")
            print("")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()

