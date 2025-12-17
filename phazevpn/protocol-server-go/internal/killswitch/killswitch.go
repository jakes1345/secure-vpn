package killswitch

import (
	"fmt"
	"log"
	"os/exec"
	"runtime"
)

// KillSwitch manages network blocking when VPN disconnects
type KillSwitch struct {
	enabled      bool
	vpnInterface string
}

// NewKillSwitch creates a new kill switch manager
func NewKillSwitch(vpnInterface string) *KillSwitch {
	return &KillSwitch{
		enabled:      false,
		vpnInterface: vpnInterface,
	}
}

// Enable activates the kill switch (blocks all non-VPN traffic)
func (ks *KillSwitch) Enable() error {
	if ks.enabled {
		return nil
	}

	log.Println("🛡️  Enabling kill switch...")

	switch runtime.GOOS {
	case "linux":
		return ks.enableLinux()
	case "darwin":
		return ks.enableDarwin()
	case "windows":
		return ks.enableWindows()
	default:
		return fmt.Errorf("unsupported OS: %s", runtime.GOOS)
	}
}

// Disable deactivates the kill switch (restores normal traffic)
func (ks *KillSwitch) Disable() error {
	if !ks.enabled {
		return nil
	}

	log.Println("🔓 Disabling kill switch...")

	switch runtime.GOOS {
	case "linux":
		return ks.disableLinux()
	case "darwin":
		return ks.disableDarwin()
	case "windows":
		return ks.disableWindows()
	default:
		return fmt.Errorf("unsupported OS: %s", runtime.GOOS)
	}
}

// Linux implementation using iptables
func (ks *KillSwitch) enableLinux() error {
	commands := [][]string{
		// Flush existing rules
		{"iptables", "-F"},
		{"iptables", "-X"},

		// Allow loopback
		{"iptables", "-A", "INPUT", "-i", "lo", "-j", "ACCEPT"},
		{"iptables", "-A", "OUTPUT", "-o", "lo", "-j", "ACCEPT"},

		// Allow VPN interface
		{"iptables", "-A", "INPUT", "-i", ks.vpnInterface, "-j", "ACCEPT"},
		{"iptables", "-A", "OUTPUT", "-o", ks.vpnInterface, "-j", "ACCEPT"},

		// Allow established connections
		{"iptables", "-A", "INPUT", "-m", "state", "--state", "ESTABLISHED,RELATED", "-j", "ACCEPT"},
		{"iptables", "-A", "OUTPUT", "-m", "state", "--state", "ESTABLISHED,RELATED", "-j", "ACCEPT"},

		// Block everything else
		{"iptables", "-P", "INPUT", "DROP"},
		{"iptables", "-P", "OUTPUT", "DROP"},
		{"iptables", "-P", "FORWARD", "DROP"},
	}

	for _, cmd := range commands {
		if err := exec.Command(cmd[0], cmd[1:]...).Run(); err != nil {
			return fmt.Errorf("failed to run %v: %w", cmd, err)
		}
	}

	ks.enabled = true
	log.Println("✅ Kill switch enabled (Linux/iptables)")
	return nil
}

func (ks *KillSwitch) disableLinux() error {
	commands := [][]string{
		// Flush all rules
		{"iptables", "-F"},
		{"iptables", "-X"},

		// Reset policies to ACCEPT
		{"iptables", "-P", "INPUT", "ACCEPT"},
		{"iptables", "-P", "OUTPUT", "ACCEPT"},
		{"iptables", "-P", "FORWARD", "ACCEPT"},
	}

	for _, cmd := range commands {
		if err := exec.Command(cmd[0], cmd[1:]...).Run(); err != nil {
			return fmt.Errorf("failed to run %v: %w", cmd, err)
		}
	}

	ks.enabled = false
	log.Println("✅ Kill switch disabled (Linux/iptables)")
	return nil
}

// macOS implementation using pf (packet filter)
func (ks *KillSwitch) enableDarwin() error {
	// Create pf rules file
	rules := fmt.Sprintf(`
# PhazeVPN Kill Switch
set block-policy drop
set skip on lo0

# Allow VPN interface
pass on %s all

# Block everything else
block drop all
`, ks.vpnInterface)

	// Write rules to temp file
	rulesFile := "/tmp/phazevpn-killswitch.pf"
	if err := exec.Command("sh", "-c", fmt.Sprintf("echo '%s' > %s", rules, rulesFile)).Run(); err != nil {
		return err
	}

	// Load rules
	if err := exec.Command("pfctl", "-f", rulesFile, "-e").Run(); err != nil {
		return err
	}

	ks.enabled = true
	log.Println("✅ Kill switch enabled (macOS/pf)")
	return nil
}

func (ks *KillSwitch) disableDarwin() error {
	if err := exec.Command("pfctl", "-d").Run(); err != nil {
		return err
	}

	ks.enabled = false
	log.Println("✅ Kill switch disabled (macOS/pf)")
	return nil
}

// Windows implementation using netsh
func (ks *KillSwitch) enableWindows() error {
	commands := [][]string{
		// Block all outbound traffic except VPN
		{"netsh", "advfirewall", "set", "allprofiles", "state", "on"},
		{"netsh", "advfirewall", "firewall", "add", "rule", "name=PhazeVPN-KillSwitch-Block", "dir=out", "action=block"},
		{"netsh", "advfirewall", "firewall", "add", "rule", "name=PhazeVPN-KillSwitch-Allow", "dir=out", "action=allow", "localip=10.9.0.0/24"},
	}

	for _, cmd := range commands {
		if err := exec.Command(cmd[0], cmd[1:]...).Run(); err != nil {
			return fmt.Errorf("failed to run %v: %w", cmd, err)
		}
	}

	ks.enabled = true
	log.Println("✅ Kill switch enabled (Windows/netsh)")
	return nil
}

func (ks *KillSwitch) disableWindows() error {
	commands := [][]string{
		{"netsh", "advfirewall", "firewall", "delete", "rule", "name=PhazeVPN-KillSwitch-Block"},
		{"netsh", "advfirewall", "firewall", "delete", "rule", "name=PhazeVPN-KillSwitch-Allow"},
	}

	for _, cmd := range commands {
		exec.Command(cmd[0], cmd[1:]...).Run() // Ignore errors on cleanup
	}

	ks.enabled = false
	log.Println("✅ Kill switch disabled (Windows/netsh)")
	return nil
}

// IsEnabled returns whether the kill switch is currently active
func (ks *KillSwitch) IsEnabled() bool {
	return ks.enabled
}
