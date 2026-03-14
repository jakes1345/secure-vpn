package handlers

import (
	"crypto/rand"
	"encoding/base64"
	"html/template"
	"log"
	"net/http"
	"os"
	"phazevpn-web/database"
	"phazevpn-web/middleware"
	"phazevpn-web/models"
)

var templates *template.Template

// appSecret is loaded once at startup from the APP_SECRET environment variable.
var appSecret string

func init() {
	// Load app secret from environment variable; warn loudly if missing.
	appSecret = os.Getenv("APP_SECRET")
	if appSecret == "" {
		log.Println("WARNING: APP_SECRET environment variable is not set. Set it to a strong random value in production.")
		appSecret = mustGenerateRandomBase64(32)
	}

	// Create custom functions for templates (Python/Jinja2 compatibility)
	funcMap := template.FuncMap{
		"qr_image": func(data string) string {
			return "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
		},
		"url_for": func(endpoint string, args ...interface{}) string {
			return "/" + endpoint
		},
		// secret returns the application secret loaded from APP_SECRET env var.
		"secret": func() string {
			return appSecret
		},
		// csrf_token generates a cryptographically random per-request CSRF token.
		"csrf_token": func() string {
			token, err := generateRandomBase64(32)
			if err != nil {
				log.Printf("WARNING: failed to generate CSRF token: %v", err)
				return ""
			}
			return token
		},
		"get_flashed_messages": func() []string {
			return []string{}
		},
		"current_user": func() interface{} {
			return nil
		},
	}

	// Load all templates recursively
	templates = template.New("").Funcs(funcMap)

	// Parse all HTML files in templates directory
	template.Must(templates.ParseGlob("templates/*.html"))
	template.Must(templates.ParseGlob("templates/**/*.html"))
}

// generateRandomBase64 returns n random bytes encoded as URL-safe base64.
func generateRandomBase64(n int) (string, error) {
	b := make([]byte, n)
	if _, err := rand.Read(b); err != nil {
		return "", err
	}
	return base64.URLEncoding.EncodeToString(b), nil
}

// mustGenerateRandomBase64 is like generateRandomBase64 but panics on error.
func mustGenerateRandomBase64(n int) string {
	s, err := generateRandomBase64(n)
	if err != nil {
		panic("failed to generate random secret: " + err.Error())
	}
	return s
}

// renderTemplate executes a named template and logs any error.
func renderTemplate(w http.ResponseWriter, name string, data interface{}) {
	if err := templates.ExecuteTemplate(w, name, data); err != nil {
		log.Printf("ERROR: failed to render template %q: %v", name, err)
		http.Error(w, "Internal server error", http.StatusInternalServerError)
	}
}

// Home renders the home page
func Home(w http.ResponseWriter, r *http.Request) {
	renderTemplate(w, "home.html", nil)
}

// Login handles login page and authentication
func Login(w http.ResponseWriter, r *http.Request) {
	if r.Method == "GET" {
		renderTemplate(w, "login.html", nil)
		return
	}

	// POST - handle login
	username := r.FormValue("username")
	password := r.FormValue("password")

	// Get user from database
	user, err := models.GetUserByUsername(database.DB, username)
	if err != nil {
		renderTemplate(w, "login.html", map[string]interface{}{
			"Error": "Invalid username or password",
		})
		return
	}

	// Check password
	if !models.CheckPassword(password, user.PasswordHash) {
		renderTemplate(w, "login.html", map[string]interface{}{
			"Error": "Invalid username or password",
		})
		return
	}

	// Generate token
	token, err := middleware.GenerateToken(user)
	if err != nil {
		http.Error(w, "Failed to generate token", http.StatusInternalServerError)
		return
	}

	// Set cookie
	middleware.SetAuthCookie(w, token)

	// Redirect to dashboard
	http.Redirect(w, r, "/dashboard", http.StatusSeeOther)
}

// Signup handles user registration
func Signup(w http.ResponseWriter, r *http.Request) {
	if r.Method == "GET" {
		renderTemplate(w, "signup.html", nil)
		return
	}

	// POST - handle signup
	username := r.FormValue("username")
	email := r.FormValue("email")
	password := r.FormValue("password")

	// Validate input
	if username == "" || email == "" || password == "" {
		renderTemplate(w, "signup.html", map[string]interface{}{
			"Error": "All fields are required",
		})
		return
	}

	// Create user
	user, err := models.CreateUser(database.DB, username, email, password)
	if err != nil {
		renderTemplate(w, "signup.html", map[string]interface{}{
			"Error": "Username or email already exists",
		})
		return
	}

	// Generate token
	token, err := middleware.GenerateToken(user)
	if err != nil {
		http.Error(w, "Failed to generate token", http.StatusInternalServerError)
		return
	}

	// Set cookie
	middleware.SetAuthCookie(w, token)

	// Redirect to dashboard
	http.Redirect(w, r, "/dashboard", http.StatusSeeOther)
}

// Logout handles user logout
func Logout(w http.ResponseWriter, r *http.Request) {
	middleware.ClearAuthCookie(w)
	http.Redirect(w, r, "/", http.StatusSeeOther)
}

// Dashboard renders the user dashboard
func Dashboard(w http.ResponseWriter, r *http.Request) {
	userID := r.Context().Value("user_id").(int)
	username := r.Context().Value("username").(string)

	// Get user's VPN clients
	clients, err := models.GetUserClients(database.DB, userID)
	if err != nil {
		clients = []models.Client{}
	}

	// Get subscription
	subscription, err := models.GetUserSubscription(database.DB, userID)
	if err != nil {
		subscription = &models.Subscription{Tier: "free"}
	}

	data := map[string]interface{}{
		"Username":     username,
		"Clients":      clients,
		"Subscription": subscription,
	}

	renderTemplate(w, "dashboard.html", data)
}

// Profile renders the user profile page
func Profile(w http.ResponseWriter, r *http.Request) {
	username := r.Context().Value("username").(string)

	data := map[string]interface{}{
		"Username": username,
	}

	renderTemplate(w, "profile.html", data)
}

// ForgotPassword handles password reset request
func ForgotPassword(w http.ResponseWriter, r *http.Request) {
	if r.Method == "GET" {
		renderTemplate(w, "forgot-password.html", nil)
		return
	}

	// POST - send reset email
	email := r.FormValue("email")

	// TODO: Generate reset token and send email
	_ = email // Use variable to avoid unused error

	renderTemplate(w, "forgot-password.html", map[string]interface{}{
		"Success": "If that email exists, we've sent a password reset link",
	})

}

// ResetPassword handles password reset
func ResetPassword(w http.ResponseWriter, r *http.Request) {
	token := r.URL.Query().Get("token")

	if r.Method == "GET" {
		renderTemplate(w, "reset-password.html", map[string]interface{}{
			"Token": token,
		})
		return
	}

	// POST - reset password
	// TODO: Implement password reset logic

	http.Redirect(w, r, "/login", http.StatusSeeOther)
}

// VerifyEmail handles email verification
func VerifyEmail(w http.ResponseWriter, r *http.Request) {
	token := r.URL.Query().Get("token")

	// TODO: Verify email token
	_ = token // Use variable to avoid unused error

	http.Redirect(w, r, "/dashboard", http.StatusSeeOther)
}
