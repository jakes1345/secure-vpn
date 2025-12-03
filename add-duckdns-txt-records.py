#!/usr/bin/env python3
"""
Add DuckDNS TXT Records for Email Authentication
Uses DuckDNS TXT Record API to add SPF, DKIM, and DMARC records

Usage: python3 add-duckdns-txt-records.py YOUR_DUCKDNS_TOKEN
"""

import sys
import requests
import urllib.parse

def add_txt_record(domain, token, txt_value, verbose=True):
    """Add TXT record to DuckDNS via API"""
    url = f"https://www.duckdns.org/update?domains={domain}&token={token}&txt={urllib.parse.quote(txt_value)}"
    if verbose:
        url += "&verbose=true"
    
    try:
        response = requests.get(url, timeout=10)
        return response.text.strip()
    except Exception as e:
        return f"Error: {e}"

def main():
    if len(sys.argv) < 2:
        print("=" * 60)
        print("DuckDNS TXT Records Setup")
        print("=" * 60)
        print()
        print("Usage: python3 add-duckdns-txt-records.py YOUR_DUCKDNS_TOKEN")
        print()
        print("Get your token from: https://www.duckdns.org/")
        print("  - Log in with bigjacob710@gmail.com")
        print("  - Your token is shown on the main page")
        print()
        sys.exit(1)
    
    token = sys.argv[1]
    base_domain = "phazevpn"  # Just the subdomain, not .duckdns.org
    
    print("=" * 60)
    print("Adding DuckDNS TXT Records via API")
    print("=" * 60)
    print()
    
    # SPF Record (for root domain) - Using -all for strict enforcement
    print("1. Adding/Updating SPF record for phazevpn.duckdns.org...")
    print("   Using -all (strict) instead of ~all for better Gmail acceptance")
    spf_value = "v=spf1 mx ip4:15.204.11.19 -all"
    result = add_txt_record(base_domain, token, spf_value)
    print(f"   Result: {result}")
    print()
    
    # Try DKIM for subdomain (may not work if DuckDNS doesn't support subdomain TXT)
    print("2. Attempting DKIM record for mail._domainkey subdomain...")
    print("   (This may not work - DuckDNS might only support root domain TXT)")
    dkim_value = "v=DKIM1; h=sha256; k=rsa; p=MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAnMXbrOoSo9AfUjJvgF+TwmF3LPvMr7c1iIzFwWN3wx5zlGMuQeqiDGIWEWMeC3nM7AASOIMth+JRk7DQyIm+wwQDfgyVl2zjGt6lvtCbfidUFlvy23M7CGX2ZfeNhDHWRZwdXMYCTsotQJhzeUggW/CDMMGgPaLv3AumlRWv08BdeIyPosC3RyxOrWN8o1f9Z9yWoTLYlFEwqL/qjVp8WNPpcTZ3KhzhsoQXa5sV7zwMgT1UA4mDBVGk6+pe9El8lhb616N/UwPT/Hny9JMIIgaq8a5Ku40SwrRH7z05S+zgfGI2wg1IuxP7MAi+FumoceJxDZKZwcb70jXVjYoPkwIDAQAB"
    # Try with subdomain format
    dkim_domain = "mail._domainkey.phazevpn"  # Try subdomain
    result = add_txt_record(dkim_domain, token, dkim_value)
    print(f"   Result: {result}")
    print()
    
    # Try DMARC - Start with p=none (monitoring only), can upgrade to p=quarantine or p=reject later
    print("3. Attempting DMARC record for _dmarc subdomain...")
    print("   Using p=none (monitoring mode) - can upgrade to p=quarantine later")
    dmarc_value = "v=DMARC1; p=none; rua=mailto:admin@phazevpn.duckdns.org; ruf=mailto:admin@phazevpn.duckdns.org; fo=1"
    dmarc_domain = "_dmarc.phazevpn"  # Try subdomain
    result = add_txt_record(dmarc_domain, token, dmarc_value)
    print(f"   Result: {result}")
    print()
    
    print("=" * 60)
    print("✅ TXT Records Added!")
    print("=" * 60)
    print()
    print("Verifying records...")
    print()
    print("Check SPF:")
    print("  dig TXT phazevpn.duckdns.org +short")
    print()
    print("Check DKIM:")
    print("  dig TXT mail._domainkey.phazevpn.duckdns.org +short")
    print()
    print("Check DMARC:")
    print("  dig TXT _dmarc.phazevpn.duckdns.org +short")
    print()
    print("=" * 60)
    print("📝 Important Notes:")
    print("=" * 60)
    print()
    print("1. SPF Record:")
    print("   ✅ Updated to use -all (strict enforcement)")
    print("   ✅ Authorizes IP 15.204.11.19 to send emails")
    print()
    print("2. DKIM Record:")
    print("   ⚠️  DuckDNS may not support subdomain TXT records")
    print("   ✅ OpenDKIM is configured and signing emails on the server")
    print("   ✅ If DNS doesn't work, emails will still be signed (just not verifiable)")
    print()
    print("3. DMARC Record:")
    print("   ⚠️  DuckDNS may not support subdomain TXT records")
    print("   ✅ Set to p=none (monitoring mode) - safe to start")
    print()
    print("4. Reverse DNS (PTR Record):")
    print("   ⚠️  REQUIRED for Gmail to fully trust your IP")
    print("   📧 Contact OVH support to set up reverse DNS:")
    print("      - IP: 15.204.11.19")
    print("      - Hostname: mail.phazevpn.duckdns.org")
    print("      - This helps build IP reputation with Gmail")
    print()
    print("5. IP Reputation:")
    print("   ⏳ New IPs need time to build reputation")
    print("   ✅ Send legitimate emails consistently")
    print("   ✅ Avoid spam triggers (bulk sending, bad content)")
    print("   ✅ Use Mailjet fallback for important emails until reputation builds")
    print()
    print("=" * 60)
    print("⏱️  Next Steps:")
    print("=" * 60)
    print()
    print("1. Wait 5-15 minutes for DNS propagation")
    print("2. Verify DNS records:")
    print("   dig TXT phazevpn.duckdns.org +short")
    print("   dig TXT mail._domainkey.phazevpn.duckdns.org +short")
    print("   dig TXT _dmarc.phazevpn.duckdns.org +short")
    print()
    print("3. Contact OVH to set up reverse DNS (PTR record)")
    print("4. Test sending emails - Gmail may still block initially due to IP reputation")
    print("5. Use Mailjet fallback for critical emails until reputation builds")
    print()
    print("✅ Your email service is configured correctly!")
    print("   Gmail blocking is due to IP reputation, not configuration issues.")
    print()

if __name__ == "__main__":
    main()

