package utils

import (
	"fmt"
	"golang.org/x/crypto/bcrypt"
	"math"
	"crypto/rand"
	"encoding/base64"
	"time"
)

// HashPassword hashes a password using bcrypt.
func HashPassword(password string) (string, error) {
	bytes, err := bcrypt.GenerateFromPassword([]byte(password), bcrypt.DefaultCost)
	return string(bytes), err
}

// CheckPasswordHash compares a plaintext password with a hashed password.
func CheckPasswordHash(password, hash string) bool {
	err := bcrypt.CompareHashAndPassword([]byte(hash), []byte(password))
	return err == nil
}

// FormatBytes formats bytes into a human-readable string (e.g., "1.5 GB").
func FormatBytes(bytesValue int64) string {
	if bytesValue < 0 {
		return "0 B"
	}

	units := []string{"B", "KB", "MB", "GB", "TB", "PB"}
	if bytesValue < 1024 {
		return fmt.Sprintf("%d %s", bytesValue, units[0])
	}

	i := int(math.Floor(math.Log(float64(bytesValue)) / math.Log(1024)))
	size := float64(bytesValue) / math.Pow(1024, float64(i))

	return fmt.Sprintf("%.2f %s", size, units[i])
}

// GenerateToken generates a secure random URL-safe token.
func GenerateToken(length int) (string, error) {
	b := make([]byte, length)
	_, err := rand.Read(b)
	if err != nil {
		return "", err
	}
	return base64.URLEncoding.EncodeToString(b), nil
}

// FormatDuration formats duration in seconds into a human-readable string (e.g., "2h 30m").
func FormatDuration(seconds int) string {
	if seconds < 0 {
		return "0s"
	}

	duration := time.Duration(seconds) * time.Second

	days := int(duration.Hours() / 24)
	hours := int(duration.Hours()) % 24
	minutes := int(duration.Minutes()) % 60
	remainingSeconds := int(duration.Seconds()) % 60

	result := ""
	if days > 0 {
		result += fmt.Sprintf("%dd ", days)
	}
	if hours > 0 {
		result += fmt.Sprintf("%dh ", hours)
	}
	if minutes > 0 {
		result += fmt.Sprintf("%dm ", minutes)
	}
	if remainingSeconds > 0 && days == 0 && hours == 0 && minutes == 0 {
		result += fmt.Sprintf("%ds", remainingSeconds)
	}

	// Trim trailing space if any
	if len(result) > 0 && result[len(result)-1] == ' ' {
		result = result[:len(result)-1]
	}
	
	return result
}
