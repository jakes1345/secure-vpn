package models

import (
	"encoding/json"
	"io/ioutil"
	"os"
	"secure-vpn/web-portal/config"
	"secure-vpn/web-portal/utils"
	"time"
)

// User represents a user in the system.
type User struct {
	Username          string    `json:"username"`
	Email             string    `json:"email"`
	PasswordHash      string    `json:"password_hash"`
	Role              string    `json:"role"` // "user", "moderator", "admin"
	IsActive          bool      `json:"is_active"`
	IsEmailVerified   bool      `json:"is_email_verified"`
	SubscriptionTier  string    `json:"subscription_tier"`
	SubscriptionExpiry time.Time `json:"subscription_expiry"`
	TwoFASecret       string    `json:"two_fa_secret"`
	CreatedAt         time.Time `json:"created_at"`
	LastLogin         time.Time `json:"last_login"`
}

// LoadUsers loads all users from the users.json file.
func LoadUsers() (map[string]User, error) {
	cfg := config.GetConfig()
	users := make(map[string]User)

	data, err := ioutil.ReadFile(cfg.UsersFile)
	if err != nil {
		if os.IsNotExist(err) {
			return users, nil // File doesn't exist, return empty map
		}
		return nil, err
	}

	err = json.Unmarshal(data, &users)
	if err != nil {
		return nil, err
	}

	return users, nil
}

// GetUserByUsername retrieves a user by their username.
func GetUserByUsername(username string) (*User, error) {
	users, err := LoadUsers()
	if err != nil {
		return nil, err
	}

	user, ok := users[username]
	if !ok {
		return nil, nil // User not found
	}

	return &user, nil
}

// AuthenticateUser checks the username and password against the stored hash.
func AuthenticateUser(username, password string) (*User, error) {
	user, err := GetUserByUsername(username)
	if err != nil {
		return nil, err
	}

	if user == nil {
		return nil, nil // User not found
	}

	if !utils.CheckPasswordHash(password, user.PasswordHash) {
		return nil, nil // Password mismatch
	}

	return user, nil
}

// SaveUsers saves the map of users back to the users.json file.
func SaveUsers(users map[string]User) error {
	cfg := config.GetConfig()

	data, err := json.MarshalIndent(users, "", "  ")
	if err != nil {
		return err
	}

	// In a real application, this should use file locking for safety
	return ioutil.WriteFile(cfg.UsersFile, data, 0644)
}

// UpdateUserLastLogin updates the user's last login time.
func UpdateUserLastLogin(username string) error {
	users, err := LoadUsers()
	if err != nil {
		return err
	}

	user, ok := users[username]
	if !ok {
		return nil // User not found, nothing to update
	}

	user.LastLogin = time.Now()
	users[username] = user

	return SaveUsers(users)
}
