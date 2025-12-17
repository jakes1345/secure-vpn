package dns

import (
	"fmt"
	"io/ioutil"
	"log"
	"os"
	"os/exec"
	"strings"
)

// DNSProtection manages DNS leak protection
type DNSProtection struct {
	vpnDNS      []string
	originalDNS []string
	backupFile  string
	enabled     bool
}

// NewDNSProtection creates a new DNS protection manager
func NewDNSProtection(vpnDNS []string) *DNSProtection {
	if len(vpnDNS) == 0 {
		vpnDNS = []string{"1.1.1.1", "1.0.0.1"} // Cloudflare DNS
	}

	return &DNSProtection{
		vpnDNS:     vpnDNS,
		backupFile: "/tmp/phazevpn-dns-backup.conf",
		enabled:    false,
	}
}

// Enable enables DNS leak protection
func (d *DNSProtection) Enable() error {
	log.Println("🔒 Enabling DNS leak protection...")

	// 1. Backup current DNS settings
	if err := d.backupDNS(); err != nil {
		return fmt.Errorf("failed to backup DNS: %w", err)
	}

	// 2. Set VPN DNS servers
	if err := d.setVPNDNS(); err != nil {
		d.restoreDNS() // Restore on failure
		return fmt.Errorf("failed to set VPN DNS: %w", err)
	}

	// 3. Add iptables rules to block non-VPN DNS
	if err := d.blockNonVPNDNS(); err != nil {
		d.restoreDNS()
		return fmt.Errorf("failed to block non-VPN DNS: %w", err)
	}

	d.enabled = true
	log.Println("✅ DNS leak protection enabled")
	return nil
}

// Disable disables DNS leak protection
func (d *DNSProtection) Disable() error {
	if !d.enabled {
		return nil
	}

	log.Println("🔓 Disabling DNS leak protection...")

	// Remove iptables rules
	d.unblockDNS()

	// Restore original DNS
	if err := d.restoreDNS(); err != nil {
		return fmt.Errorf("failed to restore DNS: %w", err)
	}

	d.enabled = false
	log.Println("✅ DNS leak protection disabled")
	return nil
}

// backupDNS backs up current DNS configuration
func (d *DNSProtection) backupDNS() error {
	// Read current resolv.conf
	data, err := ioutil.ReadFile("/etc/resolv.conf")
	if err != nil {
		return err
	}

	// Save to backup file
	if err := ioutil.WriteFile(d.backupFile, data, 0644); err != nil {
		return err
	}

	// Parse current DNS servers
	d.originalDNS = d.parseDNS(string(data))
	log.Printf("📝 Backed up DNS: %v", d.originalDNS)

	return nil
}

// setVPNDNS sets VPN DNS servers
func (d *DNSProtection) setVPNDNS() error {
	// Create new resolv.conf content
	var content strings.Builder
	content.WriteString("# PhazeVPN DNS Configuration\n")
	content.WriteString("# DO NOT EDIT - Managed by PhazeVPN\n\n")

	for _, dns := range d.vpnDNS {
		content.WriteString(fmt.Sprintf("nameserver %s\n", dns))
	}

	// Write to resolv.conf
	if err := ioutil.WriteFile("/etc/resolv.conf", []byte(content.String()), 0644); err != nil {
		return err
	}

	log.Printf("✅ Set VPN DNS: %v", d.vpnDNS)
	return nil
}

// restoreDNS restores original DNS configuration
func (d *DNSProtection) restoreDNS() error {
	// Check if backup exists
	if _, err := os.Stat(d.backupFile); os.IsNotExist(err) {
		log.Println("⚠️  No DNS backup found, skipping restore")
		return nil
	}

	// Read backup
	data, err := ioutil.ReadFile(d.backupFile)
	if err != nil {
		return err
	}

	// Restore resolv.conf
	if err := ioutil.WriteFile("/etc/resolv.conf", data, 0644); err != nil {
		return err
	}

	// Remove backup file
	os.Remove(d.backupFile)

	log.Printf("✅ Restored DNS: %v", d.originalDNS)
	return nil
}

// blockNonVPNDNS adds iptables rules to block DNS requests outside VPN
func (d *DNSProtection) blockNonVPNDNS() error {
	rules := [][]string{
		// Block UDP DNS (port 53) not going through VPN interface
		{"iptables", "-A", "OUTPUT", "-p", "udp", "--dport", "53", "!", "-o", "phaze0", "-j", "REJECT"},

		// Block TCP DNS (port 53) not going through VPN interface
		{"iptables", "-A", "OUTPUT", "-p", "tcp", "--dport", "53", "!", "-o", "phaze0", "-j", "REJECT"},

		// Block DNS over TLS (port 853)
		{"iptables", "-A", "OUTPUT", "-p", "tcp", "--dport", "853", "!", "-o", "phaze0", "-j", "REJECT"},

		// Block DNS over HTTPS to common providers
		{"iptables", "-A", "OUTPUT", "-p", "tcp", "--dport", "443", "-m", "string", "--string", "dns.google", "--algo", "bm", "-j", "REJECT"},
		{"iptables", "-A", "OUTPUT", "-p", "tcp", "--dport", "443", "-m", "string", "--string", "cloudflare-dns", "--algo", "bm", "-j", "REJECT"},
	}

	for _, rule := range rules {
		cmd := exec.Command(rule[0], rule[1:]...)
		if err := cmd.Run(); err != nil {
			log.Printf("⚠️  Failed to add rule %v: %v", rule, err)
			// Continue with other rules
		}
	}

	log.Println("✅ Added DNS leak protection iptables rules")
	return nil
}

// unblockDNS removes DNS blocking iptables rules
func (d *DNSProtection) unblockDNS() {
	rules := [][]string{
		{"iptables", "-D", "OUTPUT", "-p", "udp", "--dport", "53", "!", "-o", "phaze0", "-j", "REJECT"},
		{"iptables", "-D", "OUTPUT", "-p", "tcp", "--dport", "53", "!", "-o", "phaze0", "-j", "REJECT"},
		{"iptables", "-D", "OUTPUT", "-p", "tcp", "--dport", "853", "!", "-o", "phaze0", "-j", "REJECT"},
		{"iptables", "-D", "OUTPUT", "-p", "tcp", "--dport", "443", "-m", "string", "--string", "dns.google", "--algo", "bm", "-j", "REJECT"},
		{"iptables", "-D", "OUTPUT", "-p", "tcp", "--dport", "443", "-m", "string", "--string", "cloudflare-dns", "--algo", "bm", "-j", "REJECT"},
	}

	for _, rule := range rules {
		cmd := exec.Command(rule[0], rule[1:]...)
		cmd.Run() // Ignore errors on cleanup
	}

	log.Println("✅ Removed DNS leak protection rules")
}

// parseDNS parses DNS servers from resolv.conf content
func (d *DNSProtection) parseDNS(content string) []string {
	var servers []string
	lines := strings.Split(content, "\n")

	for _, line := range lines {
		line = strings.TrimSpace(line)
		if strings.HasPrefix(line, "nameserver") {
			parts := strings.Fields(line)
			if len(parts) >= 2 {
				servers = append(servers, parts[1])
			}
		}
	}

	return servers
}

// IsEnabled returns whether DNS protection is enabled
func (d *DNSProtection) IsEnabled() bool {
	return d.enabled
}
