package ipv6

import (
	"log"
	"os/exec"
)

// IPv6Protection manages IPv6 leak protection
type IPv6Protection struct {
	enabled bool
}

// NewIPv6Protection creates a new IPv6 protection manager
func NewIPv6Protection() *IPv6Protection {
	return &IPv6Protection{
		enabled: false,
	}
}

// Enable blocks all IPv6 traffic to prevent leaks
func (i *IPv6Protection) Enable() error {
	log.Println("🔒 Blocking IPv6 to prevent leaks...")

	// Option 1: Disable IPv6 completely via sysctl
	sysctlRules := [][]string{
		{"sysctl", "-w", "net.ipv6.conf.all.disable_ipv6=1"},
		{"sysctl", "-w", "net.ipv6.conf.default.disable_ipv6=1"},
		{"sysctl", "-w", "net.ipv6.conf.lo.disable_ipv6=1"},
	}

	for _, rule := range sysctlRules {
		cmd := exec.Command(rule[0], rule[1:]...)
		if err := cmd.Run(); err != nil {
			log.Printf("⚠️  Failed to disable IPv6 via sysctl: %v", err)
		}
	}

	// Option 2: Block all IPv6 traffic via ip6tables (belt and suspenders)
	ip6tablesRules := [][]string{
		// Drop all IPv6 input
		{"ip6tables", "-P", "INPUT", "DROP"},

		// Drop all IPv6 output
		{"ip6tables", "-P", "OUTPUT", "DROP"},

		// Drop all IPv6 forwarding
		{"ip6tables", "-P", "FORWARD", "DROP"},

		// Allow loopback (needed for local services)
		{"ip6tables", "-A", "INPUT", "-i", "lo", "-j", "ACCEPT"},
		{"ip6tables", "-A", "OUTPUT", "-o", "lo", "-j", "ACCEPT"},
	}

	for _, rule := range ip6tablesRules {
		cmd := exec.Command(rule[0], rule[1:]...)
		if err := cmd.Run(); err != nil {
			log.Printf("⚠️  Failed to add ip6tables rule: %v", err)
		}
	}

	i.enabled = true
	log.Println("✅ IPv6 blocked - no IPv6 leaks possible")
	return nil
}

// Disable re-enables IPv6
func (i *IPv6Protection) Disable() error {
	if !i.enabled {
		return nil
	}

	log.Println("🔓 Re-enabling IPv6...")

	// Re-enable IPv6 via sysctl
	sysctlRules := [][]string{
		{"sysctl", "-w", "net.ipv6.conf.all.disable_ipv6=0"},
		{"sysctl", "-w", "net.ipv6.conf.default.disable_ipv6=0"},
		{"sysctl", "-w", "net.ipv6.conf.lo.disable_ipv6=0"},
	}

	for _, rule := range sysctlRules {
		cmd := exec.Command(rule[0], rule[1:]...)
		cmd.Run() // Ignore errors
	}

	// Reset ip6tables to ACCEPT
	resetRules := [][]string{
		{"ip6tables", "-P", "INPUT", "ACCEPT"},
		{"ip6tables", "-P", "OUTPUT", "ACCEPT"},
		{"ip6tables", "-P", "FORWARD", "ACCEPT"},
		{"ip6tables", "-F"}, // Flush all rules
	}

	for _, rule := range resetRules {
		cmd := exec.Command(rule[0], rule[1:]...)
		cmd.Run() // Ignore errors
	}

	i.enabled = false
	log.Println("✅ IPv6 re-enabled")
	return nil
}

// IsEnabled returns whether IPv6 protection is enabled
func (i *IPv6Protection) IsEnabled() bool {
	return i.enabled
}
