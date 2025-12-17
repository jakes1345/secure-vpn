package handlers

import (
	"html/template"
	"net/http"
	"phazevpn-web/database"
	"phazevpn-web/middleware"
	"phazevpn-web/models"
)

var templates *template.Template

func init() {
	// Create custom functions for templates (Python/Jinja2 compatibility)
	funcMap := template.FuncMap{
		"qr_image": func(data string) string {
			return "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
		},
		"url_for": func(endpoint string, args ...interface{}) string {
			return "/" + endpoint
		},
		"secret": func() string {
			return "PLACEHOLDER_SECRET"
		},
		"csrf_token": func() string {
			return "csrf_token_placeholder"
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

// Home renders the home page
func Home(w http.ResponseWriter, r *http.Request) {
	templates.ExecuteTemplate(w, "home.html", nil)
}

// Login handles login page and authentication
func Login(w http.ResponseWriter, r *http.Request) {
	if r.Method == "GET" {
		templates.ExecuteTemplate(w, "login.html", nil)
		return
	}

	// POST - handle login
	username := r.FormValue("username")
	password := r.FormValue("password")

	// Get user from database
	user, err := models.GetUserByUsername(database.DB, username)
	if err != nil {
		templates.ExecuteTemplate(w, "login.html", map[string]interface{}{
			"Error": "Invalid username or password",
		})
		return
	}

	// Check password
	if !models.CheckPassword(password, user.PasswordHash) {
		templates.ExecuteTemplate(w, "login.html", map[string]interface{}{
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
		templates.ExecuteTemplate(w, "signup.html", nil)
		return
	}

	// POST - handle signup
	username := r.FormValue("username")
	email := r.FormValue("email")
	password := r.FormValue("password")

	// Validate input
	if username == "" || email == "" || password == "" {
		templates.ExecuteTemplate(w, "signup.html", map[string]interface{}{
			"Error": "All fields are required",
		})
		return
	}

	// Create user
	user, err := models.CreateUser(database.DB, username, email, password)
	if err != nil {
		templates.ExecuteTemplate(w, "signup.html", map[string]interface{}{
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

	templates.ExecuteTemplate(w, "dashboard.html", data)
}

// Profile renders the user profile page
func Profile(w http.ResponseWriter, r *http.Request) {
	username := r.Context().Value("username").(string)

	data := map[string]interface{}{
		"Username": username,
	}

	templates.ExecuteTemplate(w, "profile.html", data)
}

// ForgotPassword handles password reset request
func ForgotPassword(w http.ResponseWriter, r *http.Request) {
	if r.Method == "GET" {
		templates.ExecuteTemplate(w, "forgot-password.html", nil)
		return
	}

	// POST - send reset email
	email := r.FormValue("email")

	// TODO: Generate reset token and send email
	_ = email // Use variable to avoid unused error

	templates.ExecuteTemplate(w, "forgot-password.html", map[string]interface{}{
		"Success": "If that email exists, we've sent a password reset link",
	})

}

// ResetPassword handles password reset
func ResetPassword(w http.ResponseWriter, r *http.Request) {
	token := r.URL.Query().Get("token")

	if r.Method == "GET" {
		templates.ExecuteTemplate(w, "reset-password.html", map[string]interface{}{
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
