package handlers

import (
	"net/http"
	"phazevpn-web/database"
	"phazevpn-web/models"
	"strconv"

	"github.com/gorilla/mux"
)

// AdminDashboard renders the admin dashboard
func AdminDashboard(w http.ResponseWriter, r *http.Request) {
	// Get total users
	var totalUsers int
	database.DB.QueryRow("SELECT COUNT(*) FROM users").Scan(&totalUsers)

	// Get total clients
	var totalClients int
	database.DB.QueryRow("SELECT COUNT(*) FROM clients").Scan(&totalClients)

	// Get active subscriptions
	var activeSubscriptions int
	database.DB.QueryRow("SELECT COUNT(*) FROM subscriptions WHERE status = 'active'").Scan(&activeSubscriptions)

	data := map[string]interface{}{
		"TotalUsers":          totalUsers,
		"TotalClients":        totalClients,
		"ActiveSubscriptions": activeSubscriptions,
	}

	templates.ExecuteTemplate(w, "admin-dashboard.html", data)
}

// AdminUsers lists all users
func AdminUsers(w http.ResponseWriter, r *http.Request) {
	rows, err := database.DB.Query(`
		SELECT id, username, email, role, email_verified, created_at
		FROM users ORDER BY created_at DESC
	`)
	if err != nil {
		http.Error(w, "Failed to load users", http.StatusInternalServerError)
		return
	}
	defer rows.Close()

	var users []models.User
	for rows.Next() {
		var user models.User
		rows.Scan(&user.ID, &user.Username, &user.Email, &user.Role, &user.EmailVerified, &user.CreatedAt)
		users = append(users, user)
	}

	data := map[string]interface{}{
		"Users": users,
	}

	templates.ExecuteTemplate(w, "admin-users.html", data)
}

// AdminUserDetail shows details for a specific user
func AdminUserDetail(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	userID, _ := strconv.Atoi(vars["id"])

	// Get user
	var user models.User
	err := database.DB.QueryRow(`
		SELECT id, username, email, role, email_verified, created_at
		FROM users WHERE id = ?
	`, userID).Scan(&user.ID, &user.Username, &user.Email, &user.Role, &user.EmailVerified, &user.CreatedAt)

	if err != nil {
		http.Error(w, "User not found", http.StatusNotFound)
		return
	}

	// Get user's clients
	clients, _ := models.GetUserClients(database.DB, userID)

	// Get user's subscription
	subscription, _ := models.GetUserSubscription(database.DB, userID)

	data := map[string]interface{}{
		"User":         user,
		"Clients":      clients,
		"Subscription": subscription,
	}

	templates.ExecuteTemplate(w, "admin-user-detail.html", data)
}
