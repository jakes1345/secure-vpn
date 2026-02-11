package services

import (
	"fmt"
	"log"
	"net/smtp"
	"secure-vpn/web-portal/config"
)

// EmailService defines the interface for all email providers.
type EmailService interface {
	SendEmail(to, subject, body string) error
	ProviderName() string
}

// --- Fallback Service ---

// FallbackEmailService implements the primary email sending logic with fallbacks.
type FallbackEmailService struct {
	providers []EmailService
}

// NewFallbackEmailService initializes the service with configured providers.
func NewFallbackEmailService() *FallbackEmailService {
	cfg := config.GetConfig()
	providers := make([]EmailService, 0)

	// 1. Custom SMTP (highest priority)
	if cfg.SMTPHost != "" && cfg.SMTPUser != "" {
		providers = append(providers, NewSMTPService(cfg))
	}

	// Add other providers here in the future

	if len(providers) == 0 {
		log.Println("WARNING: No email providers configured. Email sending will fail.")
	}

	return &FallbackEmailService{
		providers: providers,
	}
}

// SendEmail attempts to send an email using the configured providers in order.
func (f *FallbackEmailService) SendEmail(to, subject, body string) error {
	if len(f.providers) == 0 {
		return fmt.Errorf("no email providers configured")
	}

	var lastErr error
	for _, provider := range f.providers {
		log.Printf("Attempting to send email to %s using %s...", to, provider.ProviderName())
		err := provider.SendEmail(to, subject, body)
		if err == nil {
			log.Printf("Email successfully sent to %s using %s.", to, provider.ProviderName())
			return nil // Success
		}
		log.Printf("Failed to send email using %s: %v", provider.ProviderName(), err)
		lastErr = err
	}

	return fmt.Errorf("all email providers failed to send email to %s. Last error: %w", to, lastErr)
}

// --- SMTP Service Implementation ---

// SMTPService implements the EmailService interface for custom SMTP.
type SMTPService struct {
	cfg *config.Config
}

// NewSMTPService creates a new SMTP service instance.
func NewSMTPService(cfg *config.Config) *SMTPService {
	return &SMTPService{cfg: cfg}
}

// ProviderName returns the name of the provider.
func (s *SMTPService) ProviderName() string {
	return "Custom SMTP"
}

// SendEmail implements the actual SMTP sending logic.
func (s *SMTPService) SendEmail(to, subject, body string) error {
	from := s.cfg.SMTPUser
	addr := fmt.Sprintf("%s:%d", s.cfg.SMTPHost, s.cfg.SMTPPort)

	auth := smtp.PlainAuth("", from, s.cfg.SMTPPassword, s.cfg.SMTPHost)

	msg := []byte(
		"To: " + to + "\r\n" +
		"From: " + from + "\r\n" +
		"Subject: " + subject + "\r\n" +
		"MIME-version: 1.0;\r\n" +
		"Content-Type: text/html; charset=\"UTF-8\";\r\n" +
		"\r\n" +
		body + "\r\n",
	)

	return smtp.SendMail(addr, auth, from, []string{to}, msg)
}
