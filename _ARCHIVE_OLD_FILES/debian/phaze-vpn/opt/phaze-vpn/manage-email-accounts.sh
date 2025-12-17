#!/bin/bash
# Email Account Management Script
# Add, remove, list, and manage email accounts

set -e

MYSQL_USER="mailuser"
MYSQL_PASS="mailpass"
MYSQL_DB="mailserver"
EMAIL_DOMAIN="phazevpn.duckdns.org"

function usage() {
    echo "Email Account Management"
    echo ""
    echo "Usage: $0 [command] [options]"
    echo ""
    echo "Commands:"
    echo "  add <email> [password]     - Add new email account"
    echo "  remove <email>              - Remove email account"
    echo "  list                        - List all email accounts"
    echo "  password <email> [password] - Change password"
    echo "  quota <email> <size>        - Set quota (in MB)"
    echo "  enable <email>              - Enable account"
    echo "  disable <email>             - Disable account"
    echo "  alias <source> <dest>      - Create alias"
    echo ""
    echo "Examples:"
    echo "  $0 add user@phazevpn.duckdns.org"
    echo "  $0 add user@phazevpn.duckdns.org mypassword"
    echo "  $0 list"
    echo "  $0 password user@phazevpn.duckdns.org newpass"
    echo ""
}

function add_account() {
    local email=$1
    local password=${2:-$(openssl rand -base64 12)}
    
    if [[ ! "$email" =~ ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]]; then
        echo "❌ Invalid email format: $email"
        exit 1
    fi
    
    local domain=$(echo $email | cut -d'@' -f2)
    
    # Get domain ID
    local domain_id=$(mysql -u$MYSQL_USER -p$MYSQL_PASS $MYSQL_DB -sN -e "SELECT id FROM virtual_domains WHERE name='$domain'")
    
    if [ -z "$domain_id" ]; then
        echo "📝 Creating domain: $domain"
        mysql -u$MYSQL_USER -p$MYSQL_PASS $MYSQL_DB << EOF
INSERT INTO virtual_domains (name) VALUES ('$domain');
EOF
        domain_id=$(mysql -u$MYSQL_USER -p$MYSQL_PASS $MYSQL_DB -sN -e "SELECT id FROM virtual_domains WHERE name='$domain'")
    fi
    
    # Create user
    mysql -u$MYSQL_USER -p$MYSQL_PASS $MYSQL_DB << EOF
INSERT INTO virtual_users (domain_id, email, password) 
VALUES ($domain_id, '$email', '{PLAIN}$password');
EOF
    
    # Create mail directory
    mkdir -p /var/mail/vhosts/$domain/$(echo $email | cut -d'@' -f1)
    chown -R vmail:vmail /var/mail/vhosts/$domain
    
    echo "✅ Account created: $email"
    echo "   Password: $password"
}

function remove_account() {
    local email=$1
    
    mysql -u$MYSQL_USER -p$MYSQL_PASS $MYSQL_DB << EOF
DELETE FROM virtual_users WHERE email='$email';
EOF
    
    echo "✅ Account removed: $email"
}

function list_accounts() {
    echo "📧 Email Accounts:"
    echo ""
    mysql -u$MYSQL_USER -p$MYSQL_PASS $MYSQL_DB << EOF
SELECT 
    email,
    CASE WHEN active THEN 'Active' ELSE 'Disabled' END as status,
    ROUND(quota/1048576, 2) as quota_mb
FROM virtual_users
ORDER BY email;
EOF
}

function change_password() {
    local email=$1
    local password=${2:-$(openssl rand -base64 12)}
    
    mysql -u$MYSQL_USER -p$MYSQL_PASS $MYSQL_DB << EOF
UPDATE virtual_users 
SET password = '{PLAIN}$password' 
WHERE email='$email';
EOF
    
    echo "✅ Password updated for: $email"
    echo "   New password: $password"
}

function set_quota() {
    local email=$1
    local quota_mb=$2
    local quota_bytes=$((quota_mb * 1048576))
    
    mysql -u$MYSQL_USER -p$MYSQL_PASS $MYSQL_DB << EOF
UPDATE virtual_users 
SET quota = $quota_bytes 
WHERE email='$email';
EOF
    
    echo "✅ Quota set for $email: ${quota_mb}MB"
}

function enable_account() {
    local email=$1
    
    mysql -u$MYSQL_USER -p$MYSQL_PASS $MYSQL_DB << EOF
UPDATE virtual_users 
SET active = TRUE 
WHERE email='$email';
EOF
    
    echo "✅ Account enabled: $email"
}

function disable_account() {
    local email=$1
    
    mysql -u$MYSQL_USER -p$MYSQL_PASS $MYSQL_DB << EOF
UPDATE virtual_users 
SET active = FALSE 
WHERE email='$email';
EOF
    
    echo "✅ Account disabled: $email"
}

function create_alias() {
    local source=$1
    local dest=$2
    
    local domain=$(echo $source | cut -d'@' -f2)
    local domain_id=$(mysql -u$MYSQL_USER -p$MYSQL_PASS $MYSQL_DB -sN -e "SELECT id FROM virtual_domains WHERE name='$domain'")
    
    mysql -u$MYSQL_USER -p$MYSQL_PASS $MYSQL_DB << EOF
INSERT INTO virtual_aliases (domain_id, source, destination)
VALUES ($domain_id, '$source', '$dest');
EOF
    
    echo "✅ Alias created: $source -> $dest"
}

# Main
case "$1" in
    add)
        if [ -z "$2" ]; then
            echo "❌ Email required"
            usage
            exit 1
        fi
        add_account "$2" "$3"
        ;;
    remove|delete)
        if [ -z "$2" ]; then
            echo "❌ Email required"
            usage
            exit 1
        fi
        remove_account "$2"
        ;;
    list)
        list_accounts
        ;;
    password|passwd)
        if [ -z "$2" ]; then
            echo "❌ Email required"
            usage
            exit 1
        fi
        change_password "$2" "$3"
        ;;
    quota)
        if [ -z "$2" ] || [ -z "$3" ]; then
            echo "❌ Email and quota required"
            usage
            exit 1
        fi
        set_quota "$2" "$3"
        ;;
    enable)
        if [ -z "$2" ]; then
            echo "❌ Email required"
            usage
            exit 1
        fi
        enable_account "$2"
        ;;
    disable)
        if [ -z "$2" ]; then
            echo "❌ Email required"
            usage
            exit 1
        fi
        disable_account "$2"
        ;;
    alias)
        if [ -z "$2" ] || [ -z "$3" ]; then
            echo "❌ Source and destination required"
            usage
            exit 1
        fi
        create_alias "$2" "$3"
        ;;
    *)
        usage
        exit 1
        ;;
esac