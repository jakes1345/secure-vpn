package models

import (
	"database/sql"
	"time"

	"golang.org/x/crypto/bcrypt"
)

type User struct {
	ID                int       `json:"id"`
	Username          string    `json:"username"`
	Email             string    `json:"email"`
	PasswordHash      string    `json:"-"`
	Role              string    `json:"role"`
	EmailVerified     bool      `json:"email_verified"`
	VerificationToken string    `json:"-"`
	ResetToken        string    `json:"-"`
	ResetTokenExpiry  time.Time `json:"-"`
	CreatedAt         time.Time `json:"created_at"`
	UpdatedAt         time.Time `json:"updated_at"`
}

type Client struct {
	ID         int       `json:"id"`
	UserID     int       `json:"user_id"`
	Name       string    `json:"name"`
	Protocol   string    `json:"protocol"`
	PublicKey  string    `json:"public_key,omitempty"`
	PrivateKey string    `json:"-"`
	IPAddress  string    `json:"ip_address"`
	CreatedAt  time.Time `json:"created_at"`
}

type Subscription struct {
	ID        int       `json:"id"`
	UserID    int       `json:"user_id"`
	Tier      string    `json:"tier"`
	Status    string    `json:"status"`
	ExpiresAt time.Time `json:"expires_at"`
	CreatedAt time.Time `json:"created_at"`
}

// HashPassword hashes a password using bcrypt
func HashPassword(password string) (string, error) {
	bytes, err := bcrypt.GenerateFromPassword([]byte(password), 12)
	return string(bytes), err
}

// CheckPassword compares a password with a hash
func CheckPassword(password, hash string) bool {
	err := bcrypt.CompareHashAndPassword([]byte(hash), []byte(password))
	return err == nil
}

// GetUserByUsername retrieves a user by username
func GetUserByUsername(db *sql.DB, username string) (*User, error) {
	user := &User{}
	err := db.QueryRow(`
		SELECT id, username, email, password_hash, role, email_verified, 
		       verification_token, reset_token, reset_token_expiry, created_at, updated_at
		FROM users WHERE username = ?
	`, username).Scan(
		&user.ID, &user.Username, &user.Email, &user.PasswordHash, &user.Role,
		&user.EmailVerified, &user.VerificationToken, &user.ResetToken,
		&user.ResetTokenExpiry, &user.CreatedAt, &user.UpdatedAt,
	)
	if err != nil {
		return nil, err
	}
	return user, nil
}

// GetUserByEmail retrieves a user by email
func GetUserByEmail(db *sql.DB, email string) (*User, error) {
	user := &User{}
	err := db.QueryRow(`
		SELECT id, username, email, password_hash, role, email_verified,
		       verification_token, reset_token, reset_token_expiry, created_at, updated_at
		FROM users WHERE email = ?
	`, email).Scan(
		&user.ID, &user.Username, &user.Email, &user.PasswordHash, &user.Role,
		&user.EmailVerified, &user.VerificationToken, &user.ResetToken,
		&user.ResetTokenExpiry, &user.CreatedAt, &user.UpdatedAt,
	)
	if err != nil {
		return nil, err
	}
	return user, nil
}

// CreateUser creates a new user
func CreateUser(db *sql.DB, username, email, password string) (*User, error) {
	hash, err := HashPassword(password)
	if err != nil {
		return nil, err
	}

	result, err := db.Exec(`
		INSERT INTO users (username, email, password_hash, role, email_verified, created_at, updated_at)
		VALUES (?, ?, ?, 'user', false, NOW(), NOW())
	`, username, email, hash)
	if err != nil {
		return nil, err
	}

	id, err := result.LastInsertId()
	if err != nil {
		return nil, err
	}

	return &User{
		ID:            int(id),
		Username:      username,
		Email:         email,
		Role:          "user",
		EmailVerified: false,
		CreatedAt:     time.Now(),
		UpdatedAt:     time.Now(),
	}, nil
}

// GetUserClients retrieves all VPN clients for a user
func GetUserClients(db *sql.DB, userID int) ([]Client, error) {
	rows, err := db.Query(`
		SELECT id, user_id, name, protocol, public_key, ip_address, created_at
		FROM clients WHERE user_id = ? ORDER BY created_at DESC
	`, userID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var clients []Client
	for rows.Next() {
		var c Client
		var publicKey sql.NullString
		err := rows.Scan(&c.ID, &c.UserID, &c.Name, &c.Protocol, &publicKey, &c.IPAddress, &c.CreatedAt)
		if err != nil {
			return nil, err
		}
		if publicKey.Valid {
			c.PublicKey = publicKey.String
		}
		clients = append(clients, c)
	}

	return clients, nil
}

// GetUserSubscription retrieves the active subscription for a user
func GetUserSubscription(db *sql.DB, userID int) (*Subscription, error) {
	sub := &Subscription{}
	err := db.QueryRow(`
		SELECT id, user_id, tier, status, expires_at, created_at
		FROM subscriptions WHERE user_id = ? AND status = 'active'
		ORDER BY created_at DESC LIMIT 1
	`, userID).Scan(&sub.ID, &sub.UserID, &sub.Tier, &sub.Status, &sub.ExpiresAt, &sub.CreatedAt)
	if err == sql.ErrNoRows {
		// Return free tier if no subscription
		return &Subscription{
			UserID:    userID,
			Tier:      "free",
			Status:    "active",
			CreatedAt: time.Now(),
		}, nil
	}
	if err != nil {
		return nil, err
	}
	return sub, nil
}
