package main

import (
	"fmt"
	"net/smtp"
)

const (
	SMTP_HOST     = "localhost" // Use local Postfix server
	SMTP_PORT     = "25"        // Standard SMTP port
	SMTP_USER     = ""          // No auth needed for local
	SMTP_PASSWORD = ""          // No auth needed for local
	FROM_EMAIL    = "noreply@phazevpn.com"
	FROM_NAME     = "PhazeVPN"
)

// SendEmail sends an email using local Postfix server
func SendEmail(to, subject, body string) error {
	from := fmt.Sprintf("%s <%s>", FROM_NAME, FROM_EMAIL)

	// Setup headers
	headers := make(map[string]string)
	headers["From"] = from
	headers["To"] = to
	headers["Subject"] = subject
	headers["MIME-Version"] = "1.0"
	headers["Content-Type"] = "text/html; charset=UTF-8"

	// Build message
	message := ""
	for k, v := range headers {
		message += fmt.Sprintf("%s: %s\r\n", k, v)
	}
	message += "\r\n" + body

	// Connect to local SMTP server (no auth needed)
	c, err := smtp.Dial(SMTP_HOST + ":" + SMTP_PORT)
	if err != nil {
		return err
	}
	defer c.Quit()

	// Set sender
	if err = c.Mail(FROM_EMAIL); err != nil {
		return err
	}

	// Set recipient
	if err = c.Rcpt(to); err != nil {
		return err
	}

	// Send message
	w, err := c.Data()
	if err != nil {
		return err
	}

	_, err = w.Write([]byte(message))
	if err != nil {
		return err
	}

	err = w.Close()
	if err != nil {
		return err
	}

	return nil
}

// SendVerificationEmail sends account verification email
func SendVerificationEmail(to, username, token string) error {
	subject := "Verify Your PhazeVPN Account"

	body := fmt.Sprintf(`
<!DOCTYPE html>
<html>
<head>
	<style>
		body { font-family: Arial, sans-serif; background: #0a0e27; color: #ffffff; padding: 20px; }
		.container { max-width: 600px; margin: 0 auto; background: #1a1e37; padding: 40px; border-radius: 10px; }
		.header { text-align: center; margin-bottom: 30px; }
		.logo { font-size: 32px; font-weight: bold; color: #00d4ff; }
		.button { display: inline-block; background: linear-gradient(135deg, #00d4ff, #7c3aed); color: white; padding: 15px 40px; text-decoration: none; border-radius: 50px; margin: 20px 0; font-weight: bold; }
		.footer { text-align: center; margin-top: 30px; color: #888; font-size: 12px; }
	</style>
</head>
<body>
	<div class="container">
		<div class="header">
			<div class="logo">🔒 PHAZE VPN</div>
		</div>
		<h2>Welcome to PhazeVPN, %s!</h2>
		<p>Thank you for signing up for PhazeVPN. Please verify your email address to activate your account.</p>
		<p style="text-align: center;">
			<a href="https://phazevpn.com/verify?token=%s" class="button">Verify Email Address</a>
		</p>
		<p>Or copy this link into your browser:</p>
		<p style="background: #0a0e27; padding: 10px; border-radius: 5px; word-break: break-all;">
			https://phazevpn.com/verify?token=%s
		</p>
		<p>This link will expire in 24 hours.</p>
		<div class="footer">
			<p>&copy; 2025 PhazeVPN. Zero Logs. Maximum Privacy.</p>
			<p>If you didn't create this account, please ignore this email.</p>
		</div>
	</div>
</body>
</html>
`, username, token, token)

	return SendEmail(to, subject, body)
}

// SendWelcomeEmail sends welcome email after verification
func SendWelcomeEmail(to, username string) error {
	subject := "Welcome to PhazeVPN!"

	body := fmt.Sprintf(`
<!DOCTYPE html>
<html>
<head>
	<style>
		body { font-family: Arial, sans-serif; background: #0a0e27; color: #ffffff; padding: 20px; }
		.container { max-width: 600px; margin: 0 auto; background: #1a1e37; padding: 40px; border-radius: 10px; }
		.header { text-align: center; margin-bottom: 30px; }
		.logo { font-size: 32px; font-weight: bold; color: #00d4ff; }
		.button { display: inline-block; background: linear-gradient(135deg, #00d4ff, #7c3aed); color: white; padding: 15px 40px; text-decoration: none; border-radius: 50px; margin: 20px 0; font-weight: bold; }
		.steps { background: #0a0e27; padding: 20px; border-radius: 5px; margin: 20px 0; }
		.step { margin: 15px 0; padding-left: 30px; position: relative; }
		.step:before { content: "✓"; position: absolute; left: 0; color: #00ff88; font-weight: bold; }
	</style>
</head>
<body>
	<div class="container">
		<div class="header">
			<div class="logo">🔒 PHAZE VPN</div>
		</div>
		<h2>Your Account is Ready, %s!</h2>
		<p>Your email has been verified and your account is now active. You're ready to start using PhazeVPN!</p>
		
		<div class="steps">
			<h3>Next Steps:</h3>
			<div class="step">Login to your dashboard</div>
			<div class="step">Generate your VPN keys</div>
			<div class="step">Download the client for your platform</div>
			<div class="step">Connect and enjoy private browsing!</div>
		</div>

		<p style="text-align: center;">
			<a href="https://phazevpn.com/dashboard" class="button">Go to Dashboard</a>
		</p>

		<h3>What You Get:</h3>
		<ul>
			<li>✓ Zero-knowledge VPN service</li>
			<li>✓ Multiple protocols (WireGuard, OpenVPN, PhazeVPN)</li>
			<li>✓ No logs, no tracking</li>
			<li>✓ Free during beta testing</li>
		</ul>

		<div class="footer" style="text-align: center; margin-top: 30px; color: #888; font-size: 12px;">
			<p>&copy; 2025 PhazeVPN. Zero Logs. Maximum Privacy.</p>
			<p>Need help? Visit <a href="https://phazevpn.com/contact" style="color: #00d4ff;">our support page</a></p>
		</div>
	</div>
</body>
</html>
`, username)

	return SendEmail(to, subject, body)
}

// SendPasswordResetEmail sends password reset email
func SendPasswordResetEmail(to, username, token string) error {
	subject := "Reset Your PhazeVPN Password"

	body := fmt.Sprintf(`
<!DOCTYPE html>
<html>
<head>
	<style>
		body { font-family: Arial, sans-serif; background: #0a0e27; color: #ffffff; padding: 20px; }
		.container { max-width: 600px; margin: 0 auto; background: #1a1e37; padding: 40px; border-radius: 10px; }
		.header { text-align: center; margin-bottom: 30px; }
		.logo { font-size: 32px; font-weight: bold; color: #00d4ff; }
		.button { display: inline-block; background: linear-gradient(135deg, #00d4ff, #7c3aed); color: white; padding: 15px 40px; text-decoration: none; border-radius: 50px; margin: 20px 0; font-weight: bold; }
		.warning { background: rgba(255, 0, 110, 0.1); border: 1px solid #ff006e; padding: 15px; border-radius: 5px; margin: 20px 0; }
	</style>
</head>
<body>
	<div class="container">
		<div class="header">
			<div class="logo">🔒 PHAZE VPN</div>
		</div>
		<h2>Password Reset Request</h2>
		<p>Hi %s,</p>
		<p>We received a request to reset your PhazeVPN password. Click the button below to create a new password:</p>
		<p style="text-align: center;">
			<a href="https://phazevpn.com/reset-password?token=%s" class="button">Reset Password</a>
		</p>
		<p>Or copy this link into your browser:</p>
		<p style="background: #0a0e27; padding: 10px; border-radius: 5px; word-break: break-all;">
			https://phazevpn.com/reset-password?token=%s
		</p>
		<div class="warning">
			<strong>⚠️ Security Notice:</strong>
			<p>This link will expire in 1 hour. If you didn't request a password reset, please ignore this email and your password will remain unchanged.</p>
		</div>
		<div class="footer" style="text-align: center; margin-top: 30px; color: #888; font-size: 12px;">
			<p>&copy; 2025 PhazeVPN. Zero Logs. Maximum Privacy.</p>
		</div>
	</div>
</body>
</html>
`, username, token, token)

	return SendEmail(to, subject, body)
}
