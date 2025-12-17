package main

import (
	"database/sql"
	"encoding/json"
	"fmt"
	"html/template"
	"log"
	"net/http"
	"strings"
	"time"

	_ "github.com/mattn/go-sqlite3"
)

var (
	db        *sql.DB
	templates *template.Template
)

func init() {
	// Initialize database
	var err error
	db, err = sql.Open("sqlite3", "./phazevpn.db")
	if err != nil {
		log.Fatal(err)
	}

	// Create tables
	createTables()

	// Load templates
	templates = template.Must(template.ParseGlob("templates/*.html"))
}

func createTables() {
	schema := `
	CREATE TABLE IF NOT EXISTS users (
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		username TEXT UNIQUE NOT NULL,
		email TEXT UNIQUE NOT NULL,
		password_hash TEXT NOT NULL,
		created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
		is_verified BOOLEAN DEFAULT 0,
		verification_token TEXT,
		reset_token TEXT,
		reset_token_expires DATETIME
	);

	CREATE TABLE IF NOT EXISTS vpn_keys (
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		user_id INTEGER NOT NULL,
		device_name TEXT NOT NULL,
		public_key TEXT NOT NULL,
		created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
		FOREIGN KEY (user_id) REFERENCES users(id)
	);

	CREATE TABLE IF NOT EXISTS sessions (
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		user_id INTEGER NOT NULL,
		token TEXT UNIQUE NOT NULL,
		expires_at DATETIME NOT NULL,
		FOREIGN KEY (user_id) REFERENCES users(id)
	);
	`
	_, err := db.Exec(schema)
	if err != nil {
		log.Fatal(err)
	}

	// Migration: Add new columns if they don't exist
	migrateDB()
}

func migrateDB() {
	// Add is_verified if missing
	_, err := db.Exec("ALTER TABLE users ADD COLUMN is_verified BOOLEAN DEFAULT 0")
	if err != nil && !strings.Contains(err.Error(), "duplicate column") {
		// Ignore duplicate column error, log others
		log.Println("Migration warning (is_verified):", err)
	}

	// Add verification_token
	_, err = db.Exec("ALTER TABLE users ADD COLUMN verification_token TEXT")
	if err != nil && !strings.Contains(err.Error(), "duplicate column") {
		log.Println("Migration warning (verification_token):", err)
	}

	// Add reset_token
	_, err = db.Exec("ALTER TABLE users ADD COLUMN reset_token TEXT")
	if err != nil && !strings.Contains(err.Error(), "duplicate column") {
		log.Println("Migration warning (reset_token):", err)
	}

	// Add reset_token_expires
	_, err = db.Exec("ALTER TABLE users ADD COLUMN reset_token_expires DATETIME")
	if err != nil && !strings.Contains(err.Error(), "duplicate column") {
		log.Println("Migration warning (reset_token_expires):", err)
	}
}

func main() {
	// Static files
	fs := http.FileServer(http.Dir("./static"))
	http.Handle("/static/", http.StripPrefix("/static/", fs))

	// Public Routes
	http.HandleFunc("/", homeHandler)
	http.HandleFunc("/login", loginHandler)
	http.HandleFunc("/signup", signupHandler)
	http.HandleFunc("/verify", verifyEmailHandler)
	http.HandleFunc("/forgot-password", forgotPasswordHandler)
	http.HandleFunc("/reset-password", resetPasswordHandler)
	http.HandleFunc("/logout", logoutHandler)
	http.HandleFunc("/download", downloadHandler)
	http.HandleFunc("/pricing", pricingHandler)
	http.HandleFunc("/faq", faqHandler)
	http.HandleFunc("/contact", contactHandler)
	http.HandleFunc("/terms", termsHandler)
	http.HandleFunc("/privacy", privacyHandler)
	http.HandleFunc("/transparency", transparencyHandler)
	http.HandleFunc("/phazebrowser", phazebrowserHandler)
	http.HandleFunc("/os", osHandler)
	http.HandleFunc("/blog", blogHandler)
	http.HandleFunc("/testimonials", testimonialsHandler)
	http.HandleFunc("/status", statusHandler)

	// Protected Routes
	http.HandleFunc("/dashboard", authRequired(dashboardHandler))
	http.HandleFunc("/profile", authRequired(profileHandler))
	http.HandleFunc("/vpn/generate", authRequired(generateVPNKeysHandler))
	http.HandleFunc("/vpn/download/wireguard", authRequired(downloadWireGuardHandler))
	http.HandleFunc("/vpn/download/openvpn", authRequired(downloadOpenVPNHandler))
	http.HandleFunc("/vpn/download/phazevpn", authRequired(downloadPhazeVPNHandler))

	// API Routes for GUI Client
	http.HandleFunc("/api/login", apiLoginHandler)
	http.HandleFunc("/api/vpn/keys", authRequired(apiGetVPNKeysHandler))

	log.Println("🚀 PhazeVPN Web Server starting on :5000")
	log.Fatal(http.ListenAndServe(":5000", nil))
}

// Middleware
func authRequired(next http.HandlerFunc) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		cookie, err := r.Cookie("session_token")
		if err != nil {
			http.Redirect(w, r, "/login", http.StatusSeeOther)
			return
		}

		var userID int
		var expiresAt time.Time
		err = db.QueryRow("SELECT user_id, expires_at FROM sessions WHERE token = ?", cookie.Value).Scan(&userID, &expiresAt)
		if err != nil || time.Now().After(expiresAt) {
			http.Redirect(w, r, "/login", http.StatusSeeOther)
			return
		}

		next(w, r)
	}
}

// Handlers
func homeHandler(w http.ResponseWriter, r *http.Request) {
	templates.ExecuteTemplate(w, "home.html", nil)
}

func loginHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method == "GET" {
		templates.ExecuteTemplate(w, "login.html", nil)
		return
	}

	// Handle POST
	username := r.FormValue("username")
	password := r.FormValue("password")

	var userID int
	var passwordHash string
	err := db.QueryRow("SELECT id, password_hash FROM users WHERE username = ?", username).Scan(&userID, &passwordHash)
	if err != nil {
		templates.ExecuteTemplate(w, "login.html", map[string]string{"Error": "Invalid credentials"})
		return
	}

	// Check password
	if !CheckPasswordHash(password, passwordHash) {
		templates.ExecuteTemplate(w, "login.html", map[string]string{"Error": "Invalid credentials"})
		return
	}

	// Create session
	token := generateToken()
	expiresAt := time.Now().Add(24 * time.Hour)
	_, err = db.Exec("INSERT INTO sessions (user_id, token, expires_at) VALUES (?, ?, ?)", userID, token, expiresAt)
	if err != nil {
		http.Error(w, "Server error", 500)
		return
	}

	http.SetCookie(w, &http.Cookie{
		Name:     "session_token",
		Value:    token,
		Expires:  expiresAt,
		HttpOnly: true,
		Secure:   true,
		SameSite: http.SameSiteStrictMode,
	})

	http.Redirect(w, r, "/dashboard", http.StatusSeeOther)
}

func signupHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method == "GET" {
		templates.ExecuteTemplate(w, "signup.html", nil)
		return
	}

	username := r.FormValue("username")
	email := r.FormValue("email")
	password := r.FormValue("password")

	// Hash password
	hashedPassword, err := HashPassword(password)
	if err != nil {
		http.Error(w, "Server error", 500)
		return
	}

	// Generate verification token
	verificationToken := generateToken()

	// Create user
	_, err = db.Exec("INSERT INTO users (username, email, password_hash, verification_token, is_verified) VALUES (?, ?, ?, ?, 0)",
		username, email, hashedPassword, verificationToken)
	if err != nil {
		log.Println("Signup error:", err)
		templates.ExecuteTemplate(w, "signup.html", map[string]string{"Error": "Username or email already exists"})
		return
	}

	// Send verification email
	go func() {
		err := SendVerificationEmail(email, username, verificationToken)
		if err != nil {
			log.Println("Failed to send verification email:", err)
		}
	}()

	// Show check email page
	templates.ExecuteTemplate(w, "check_email.html", nil)
}

func verifyEmailHandler(w http.ResponseWriter, r *http.Request) {
	token := r.URL.Query().Get("token")
	if token == "" {
		http.Error(w, "Invalid token", 400)
		return
	}

	// Verify user
	var username, email string
	err := db.QueryRow("SELECT username, email FROM users WHERE verification_token = ?", token).Scan(&username, &email)
	if err != nil {
		http.Error(w, "Invalid or expired token", 400)
		return
	}

	// Update user status
	_, err = db.Exec("UPDATE users SET is_verified = 1, verification_token = NULL WHERE verification_token = ?", token)
	if err != nil {
		http.Error(w, "Server error", 500)
		return
	}

	// Send welcome email
	go func() {
		err := SendWelcomeEmail(email, username)
		if err != nil {
			log.Println("Failed to send welcome email:", err)
		}
	}()

	templates.ExecuteTemplate(w, "verify_success.html", nil)
}

func forgotPasswordHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method == "GET" {
		templates.ExecuteTemplate(w, "forgot_password.html", nil)
		return
	}

	email := r.FormValue("email")

	var username string
	err := db.QueryRow("SELECT username FROM users WHERE email = ?", email).Scan(&username)
	if err != nil {
		// Don't reveal if email exists, just show success message
		templates.ExecuteTemplate(w, "forgot_password.html", map[string]string{
			"Message": "If an account exists with that email, we've sent a reset link.",
		})
		return
	}

	// Generate reset token
	resetToken := generateToken()
	expiresAttr := time.Now().Add(1 * time.Hour)

	_, err = db.Exec("UPDATE users SET reset_token = ?, reset_token_expires = ? WHERE email = ?",
		resetToken, expiresAttr, email)
	if err != nil {
		http.Error(w, "Server error", 500)
		return
	}

	// Send email
	go func() {
		err := SendPasswordResetEmail(email, username, resetToken)
		if err != nil {
			log.Println("Failed to send reset email:", err)
		}
	}()

	templates.ExecuteTemplate(w, "forgot_password.html", map[string]string{
		"Message": "If an account exists with that email, we've sent a reset link.",
	})
}

func resetPasswordHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method == "GET" {
		token := r.URL.Query().Get("token")
		if token == "" {
			http.Error(w, "Invalid token", 400)
			return
		}
		templates.ExecuteTemplate(w, "reset_password.html", map[string]string{"Token": token})
		return
	}

	token := r.FormValue("token")
	password := r.FormValue("password")

	// Verify token and expiration
	var id int
	err := db.QueryRow("SELECT id FROM users WHERE reset_token = ? AND reset_token_expires > ?", token, time.Now()).Scan(&id)
	if err != nil {
		templates.ExecuteTemplate(w, "reset_password.html", map[string]string{
			"Token": token,
			"Error": "Invalid or expired reset link. Please request a new one.",
		})
		return
	}

	// Hash new password
	hashedPassword, err := HashPassword(password)
	if err != nil {
		http.Error(w, "Server error", 500)
		return
	}

	// Update password and clear token
	_, err = db.Exec("UPDATE users SET password_hash = ?, reset_token = NULL, reset_token_expires = NULL WHERE id = ?",
		hashedPassword, id)
	if err != nil {
		http.Error(w, "Server error", 500)
		return
	}

	templates.ExecuteTemplate(w, "password_reset_success.html", nil)
}

func logoutHandler(w http.ResponseWriter, r *http.Request) {
	cookie, _ := r.Cookie("session_token")
	if cookie != nil {
		db.Exec("DELETE FROM sessions WHERE token = ?", cookie.Value)
	}

	http.SetCookie(w, &http.Cookie{
		Name:     "session_token",
		Value:    "",
		Expires:  time.Now().Add(-1 * time.Hour),
		HttpOnly: true,
	})

	http.Redirect(w, r, "/", http.StatusSeeOther)
}

func dashboardHandler(w http.ResponseWriter, r *http.Request) {
	cookie, _ := r.Cookie("session_token")
	var username string
	db.QueryRow(`
		SELECT u.username FROM users u
		JOIN sessions s ON u.id = s.user_id
		WHERE s.token = ?
	`, cookie.Value).Scan(&username)

	data := map[string]interface{}{
		"Username": username,
	}

	templates.ExecuteTemplate(w, "dashboard.html", data)
}

func profileHandler(w http.ResponseWriter, r *http.Request) {
	templates.ExecuteTemplate(w, "profile.html", nil)
}

func downloadHandler(w http.ResponseWriter, r *http.Request) {
	templates.ExecuteTemplate(w, "download.html", nil)
}

// Additional page handlers
func pricingHandler(w http.ResponseWriter, r *http.Request) {
	templates.ExecuteTemplate(w, "pricing.html", nil)
}

func faqHandler(w http.ResponseWriter, r *http.Request) {
	templates.ExecuteTemplate(w, "faq.html", nil)
}

func contactHandler(w http.ResponseWriter, r *http.Request) {
	templates.ExecuteTemplate(w, "contact.html", nil)
}

func termsHandler(w http.ResponseWriter, r *http.Request) {
	templates.ExecuteTemplate(w, "terms.html", nil)
}

func privacyHandler(w http.ResponseWriter, r *http.Request) {
	templates.ExecuteTemplate(w, "privacy.html", nil)
}

func transparencyHandler(w http.ResponseWriter, r *http.Request) {
	templates.ExecuteTemplate(w, "transparency.html", nil)
}

func phazebrowserHandler(w http.ResponseWriter, r *http.Request) {
	templates.ExecuteTemplate(w, "phazebrowser.html", nil)
}

func osHandler(w http.ResponseWriter, r *http.Request) {
	templates.ExecuteTemplate(w, "os.html", nil)
}

func blogHandler(w http.ResponseWriter, r *http.Request) {
	templates.ExecuteTemplate(w, "blog.html", nil)
}

func testimonialsHandler(w http.ResponseWriter, r *http.Request) {
	templates.ExecuteTemplate(w, "testimonials.html", nil)
}

func statusHandler(w http.ResponseWriter, r *http.Request) {
	templates.ExecuteTemplate(w, "status.html", nil)
}

// VPN Key Generation and Download Handlers
func generateVPNKeysHandler(w http.ResponseWriter, r *http.Request) {
	cookie, _ := r.Cookie("session_token")
	var userID int
	var username string
	db.QueryRow(`
		SELECT u.id, u.username FROM users u
		JOIN sessions s ON u.id = s.user_id
		WHERE s.token = ?
	`, cookie.Value).Scan(&userID, &username)

	// Generate WireGuard keys
	wgPriv, wgPub, _ := GenerateWireGuardKeys()

	// Generate PhazeVPN key
	phazeKey, _ := GeneratePhazeVPNKey()

	// Store keys in database
	db.Exec(`INSERT OR REPLACE INTO vpn_keys (user_id, device_name, public_key) VALUES (?, ?, ?)`,
		userID, "wireguard", wgPriv+"|"+wgPub)
	db.Exec(`INSERT OR REPLACE INTO vpn_keys (user_id, device_name, public_key) VALUES (?, ?, ?)`,
		userID, "phazevpn", phazeKey)

	http.Redirect(w, r, "/dashboard", http.StatusSeeOther)
}

func downloadWireGuardHandler(w http.ResponseWriter, r *http.Request) {
	cookie, _ := r.Cookie("session_token")
	var userID int
	db.QueryRow(`
		SELECT u.id FROM users u
		JOIN sessions s ON u.id = s.user_id
		WHERE s.token = ?
	`, cookie.Value).Scan(&userID)

	var keys string
	db.QueryRow("SELECT public_key FROM vpn_keys WHERE user_id = ? AND device_name = 'wireguard'", userID).Scan(&keys)

	parts := strings.Split(keys, "|")
	if len(parts) != 2 {
		http.Error(w, "Keys not generated", 400)
		return
	}

	config := CreateWireGuardConfig(parts[0], "SERVER_PUBLIC_KEY_HERE", "10.7.0."+fmt.Sprint(userID+10))

	w.Header().Set("Content-Type", "application/x-wireguard-profile")
	w.Header().Set("Content-Disposition", "attachment; filename=phazevpn.conf")
	w.Write([]byte(config))
}

func downloadOpenVPNHandler(w http.ResponseWriter, r *http.Request) {
	cookie, _ := r.Cookie("session_token")
	var username string
	db.QueryRow(`
		SELECT u.username FROM users u
		JOIN sessions s ON u.id = s.user_id
		WHERE s.token = ?
	`, cookie.Value).Scan(&username)

	config := CreateOpenVPNConfig(username)

	w.Header().Set("Content-Type", "application/x-openvpn-profile")
	w.Header().Set("Content-Disposition", "attachment; filename=phazevpn.ovpn")
	w.Write([]byte(config))
}

func downloadPhazeVPNHandler(w http.ResponseWriter, r *http.Request) {
	cookie, _ := r.Cookie("session_token")
	var userID int
	var username string
	db.QueryRow(`
		SELECT u.id, u.username FROM users u
		JOIN sessions s ON u.id = s.user_id
		WHERE s.token = ?
	`, cookie.Value).Scan(&userID, &username)

	var phazeKey string
	db.QueryRow("SELECT public_key FROM vpn_keys WHERE user_id = ? AND device_name = 'phazevpn'", userID).Scan(&phazeKey)

	config := CreatePhazeVPNConfig(username, phazeKey)

	w.Header().Set("Content-Type", "text/plain")
	w.Header().Set("Content-Disposition", "attachment; filename=phazevpn.conf")
	w.Write([]byte(config))
}

// API Handlers for GUI Client
func apiLoginHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != "POST" {
		http.Error(w, "Method not allowed", 405)
		return
	}

	var loginReq struct {
		Username string `json:"username"`
		Password string `json:"password"`
	}

	if err := json.NewDecoder(r.Body).Decode(&loginReq); err != nil {
		http.Error(w, "Invalid request", 400)
		return
	}

	// Get user from database
	var userID int
	var passwordHash string
	err := db.QueryRow("SELECT id, password_hash FROM users WHERE username = ?", loginReq.Username).Scan(&userID, &passwordHash)
	if err != nil {
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(map[string]string{"error": "Invalid credentials"})
		return
	}

	// Check password
	if !CheckPasswordHash(loginReq.Password, passwordHash) {
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(map[string]string{"error": "Invalid credentials"})
		return
	}

	// Generate token
	token := generateToken()
	expiresAt := time.Now().Add(24 * time.Hour)
	_, err = db.Exec("INSERT INTO sessions (user_id, token, expires_at) VALUES (?, ?, ?)", userID, token, expiresAt)
	if err != nil {
		http.Error(w, "Server error", 500)
		return
	}

	// Return token
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{
		"token":    token,
		"username": loginReq.Username,
	})
}

func apiGetVPNKeysHandler(w http.ResponseWriter, r *http.Request) {
	cookie, _ := r.Cookie("session_token")
	var userID int
	var username string
	db.QueryRow(`
		SELECT u.id, u.username FROM users u
		JOIN sessions s ON u.id = s.user_id
		WHERE s.token = ?
	`, cookie.Value).Scan(&userID, &username)

	// Get VPN keys
	var wgKeys, phazeKey string
	db.QueryRow("SELECT public_key FROM vpn_keys WHERE user_id = ? AND device_name = 'wireguard'", userID).Scan(&wgKeys)
	db.QueryRow("SELECT public_key FROM vpn_keys WHERE user_id = ? AND device_name = 'phazevpn'", userID).Scan(&phazeKey)

	// Parse WireGuard keys
	wgParts := strings.Split(wgKeys, "|")
	var wgPriv, wgPub string
	if len(wgParts) == 2 {
		wgPriv = wgParts[0]
		wgPub = wgParts[1]
	}

	// Return keys
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"username": username,
		"wireguard": map[string]string{
			"private_key": wgPriv,
			"public_key":  wgPub,
			"client_ip":   fmt.Sprintf("10.7.0.%d", userID+10),
		},
		"phazevpn": map[string]string{
			"key":       phazeKey,
			"client_ip": fmt.Sprintf("10.9.0.%d", userID+10),
		},
		"server": map[string]interface{}{
			"address":        "phazevpn.com",
			"wireguard_port": 51820,
			"openvpn_port":   1194,
			"phazevpn_port":  51821,
		},
	})
}
