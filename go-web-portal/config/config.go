package config

import (
	"os"
	"path/filepath"
	"strconv"
	"time"
)

// Config holds the centralized application configuration.
type Config struct {
	BaseDir             string
	WebPortalDir        string
	VpnDir              string
	
	// File Paths
	UsersFile           string
	ClientConfigsDir    string
	LogsDir             string
	StatusLog           string
	ActivityLog         string
	ConnectionHistory   string
	PaymentRequestsFile string
	TicketsFile         string

	// Flask/Web Configuration
	SecretKey           string
	IsHTTPS             bool
	SessionCookieName   string
	SessionLifetime     time.Duration

	// VPN Server Configuration
	VpnServerIP         string
	VpnServerPort       int

	// Database Configuration
	DBConfigFile        string

	// Email Configuration
	EmailProvider       string
	MailgunAPIKey       string
	MailgunDomain       string
	SMTPHost            string
	SMTPPort            int
	SMTPUser            string
	SMTPPassword        string
	SMTPUseTLS          bool

	// Rate Limiting
	RateLimitEnabled    bool
	RateLimitMaxRequests int
	RateLimitWindowSeconds int
}

// LoadConfig loads configuration from environment variables and sets defaults.
func LoadConfig() *Config {
	// Base paths
	baseDir, _ := os.Getwd() // Assuming execution from secure-vpn/go-web-portal
	webPortalDir := filepath.Join(baseDir, "web-portal")
	
	// Determine the base directory for VPN data files
	vpnDir := filepath.Join(baseDir, "vpn_data")
	
	// If running outside the project directory (e.g., as a service), use /opt/phaze-vpn
	// For now, we'll stick to a local directory for development/testing
	// if _, err := os.Stat(filepath.Join(baseDir, "vpn-manager.py")); os.IsNotExist(err) {
	// 	vpnDir = "/opt/phaze-vpn" // Default for VPS
	// }
	
	// Ensure the base VPN data directory exists
	os.MkdirAll(vpnDir, 0755)

	// Helper function to get environment variable or default string
	getEnv := func(key, defaultValue string) string {
		if value := os.Getenv(key); value != "" {
			return value
		}
		return defaultValue
	}

	// Helper function to get environment variable or default boolean
	getEnvBool := func(key string, defaultValue bool) bool {
		value := os.Getenv(key)
		if value == "" {
			return defaultValue
		}
		return value == "true" || value == "1"
	}

	// Helper function to get environment variable or default integer
	getEnvInt := func(key string, defaultValue int) int {
		value := os.Getenv(key)
		if value != "" {
			if i, err := strconv.Atoi(value); err == nil {
				return i
			}
		}
		return defaultValue
	}

	// Helper function to get environment variable or default duration
	getEnvDuration := func(key string, defaultValue time.Duration) time.Duration {
		value := os.Getenv(key)
		if value != "" {
			if d, err := time.ParseDuration(value); err == nil {
				return d
			}
		}
		return defaultValue
	}

	isHTTPS := getEnvBool("HTTPS_ENABLED", false)
	sessionCookieName := "VPN-Session"
	if isHTTPS {
		sessionCookieName = "__Secure-VPN-Session"
	}

	cfg := &Config{
		BaseDir: baseDir,
		WebPortalDir: webPortalDir,
		VpnDir: vpnDir,

		// File Paths
		UsersFile:           filepath.Join(vpnDir, "users.json"),
		ClientConfigsDir:    filepath.Join(vpnDir, "client-configs"),
		LogsDir:             filepath.Join(vpnDir, "logs"),
		StatusLog:           filepath.Join(vpnDir, "logs", "status.log"),
		ActivityLog:         filepath.Join(vpnDir, "logs", "activity.log"),
		ConnectionHistory:   filepath.Join(vpnDir, "logs", "connection-history.json"),
		PaymentRequestsFile: filepath.Join(vpnDir, "logs", "payment-requests.json"),
		TicketsFile:         filepath.Join(vpnDir, "logs", "tickets.json"),

		// Web Configuration
		SecretKey:           getEnv("FLASK_SECRET_KEY", "Y8Kp3mN9qR2vX7wL5zA6bC4dE1fG8hI0jK2lM6nO4pQ9rS3tU7vW1xY5zA8bC0dE2fG4hI6jK8lM0nO2pQ4rS6tU8vW0xY2zA4bC6dE8fG0hI2jK4lM6nO8pQ0rS2tU4vW6xY8zA0bC2dE4"),
		IsHTTPS:             isHTTPS,
		SessionCookieName:   sessionCookieName,
		SessionLifetime:     getEnvDuration("SESSION_LIFETIME", 8*time.Hour),

		// VPN Server Configuration
		VpnServerIP:         getEnv("VPN_SERVER_IP", "phazevpn.com"),
		VpnServerPort:       getEnvInt("VPN_SERVER_PORT", 1194),

		// Database Configuration
		DBConfigFile:        filepath.Join(webPortalDir, "db_config.json"),

		// Email Configuration
		EmailProvider:       getEnv("EMAIL_PROVIDER", "mailgun"),
		MailgunAPIKey:       getEnv("MAILGUN_API_KEY", ""),
		MailgunDomain:       getEnv("MAILGUN_DOMAIN", ""),
		SMTPHost:            getEnv("SMTP_HOST", ""),
		SMTPPort:            getEnvInt("SMTP_PORT", 587),
		SMTPUser:            getEnv("SMTP_USER", ""),
		SMTPPassword:        getEnv("SMTP_PASSWORD", ""),
		SMTPUseTLS:          getEnvBool("SMTP_USE_TLS", true),

		// Rate Limiting
		RateLimitEnabled:    getEnvBool("RATE_LIMIT_ENABLED", true),
		RateLimitMaxRequests: getEnvInt("RATE_LIMIT_MAX_REQUESTS", 100),
		RateLimitWindowSeconds: getEnvInt("RATE_LIMIT_WINDOW_SECONDS", 3600),
	}

	return cfg
}

// GetConfig returns the loaded configuration (singleton pattern)
var globalConfig *Config

func GetConfig() *Config {
	if globalConfig == nil {
		globalConfig = LoadConfig()
	}
	return globalConfig
}
