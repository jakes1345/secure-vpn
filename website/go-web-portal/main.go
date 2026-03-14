package main

import (
	"fmt"
	"log"
	"net/http"
	"os"
	"regexp"
	"secure-vpn/web-portal/config"
	"secure-vpn/web-portal/models"
	"secure-vpn/web-portal/utils"

	"github.com/gin-gonic/gin"
)

// allowedProtocols is the set of valid VPN protocol names accepted by GetClientConfigHandler.
var allowedProtocols = map[string]bool{
	"wireguard": true,
	"openvpn":   true,
	"phazevpn":  true,
}

// safeIdentifier matches strings that are safe for use as filename components
// (alphanumeric, hyphens, underscores only — no path separators or special chars).
var safeIdentifier = regexp.MustCompile(`^[a-zA-Z0-9_\-]+$`)

// LoginRequest defines the structure for the login request body.
type LoginRequest struct {
	Username string `json:"username" binding:"required"`
	Password string `json:"password" binding:"required"`
}

// LoginHandler handles user login requests.
func LoginHandler(c *gin.Context) {
	var req LoginRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid request body"})
		return
	}

	user, err := models.AuthenticateUser(req.Username, req.Password)
	if err != nil {
		log.Printf("Error authenticating user %s: %v", req.Username, err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Internal server error"})
		return
	}

	if user == nil {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "Invalid username or password"})
		return
	}
	// Authentication successful
	models.UpdateUserLastLogin(user.Username) // Update last login time (ignoring error for now)

	token, err := utils.GenerateToken(32)
	if err != nil {
		log.Printf("Error generating token: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Internal server error"})
		return
	}

	// In a real app, you would set a secure session cookie or return a JWT
	c.JSON(http.StatusOK, gin.H{
		"message": "Login successful",
		"user":    user.Username,
		"role":    user.Role,
		"token":   token,
	})
}

// GetClientConfigHandler handles requests for client configuration files.
func GetClientConfigHandler(c *gin.Context) {
	// TODO: implement proper token-based authentication before serving configs.
	// WARNING: this endpoint is currently unauthenticated.
	log.Println("WARNING: GetClientConfigHandler called without authentication")

	username := c.Query("username")
	clientID := c.Query("client_id")
	protocol := c.Query("protocol")

	if username == "" || clientID == "" || protocol == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Missing username, client_id, or protocol"})
		return
	}

	// Validate protocol against allowlist to prevent injection.
	if !allowedProtocols[protocol] {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid protocol; must be one of: wireguard, openvpn, phazevpn"})
		return
	}

	// Validate username and client_id to prevent path traversal or header injection.
	if !safeIdentifier.MatchString(username) || !safeIdentifier.MatchString(clientID) {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid characters in username or client_id"})
		return
	}

	configData, err := models.GetClientConfig(username, clientID, protocol)
	if err != nil {
		log.Printf("Error getting client config for %s/%s: %v", username, clientID, err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to retrieve configuration"})
		return
	}

	// Set headers for file download — filename is safe because both components
	// were validated against safeIdentifier above (alphanumeric, hyphens, underscores).
	// RFC 6266: use "filename=<quoted-string>" with double quotes.
	filename := fmt.Sprintf("%s_%s.%s", username, clientID, protocol)
	c.Header("Content-Disposition", fmt.Sprintf(`attachment; filename="%s"`, filename))
	c.Data(http.StatusOK, "application/octet-stream", configData)
}

// SetupRouter sets up the Gin router with all routes.
func SetupRouter() *gin.Engine {
	router := gin.Default()

	// Simple API group
	api := router.Group("/api/v1")
	{
		api.POST("/login", LoginHandler)
		api.GET("/client/config", GetClientConfigHandler)
		// Add other API routes here
	}

	return router
}

func main() {
	cfg := config.GetConfig()

	// Set Gin mode based on environment
	if os.Getenv("GIN_MODE") == "" {
		if cfg.IsHTTPS {
			gin.SetMode(gin.ReleaseMode)
		} else {
			gin.SetMode(gin.DebugMode)
		}
	}

	// Print config for debugging
	fmt.Println("--- SecureVPN Go Web Portal Configuration ---")
	fmt.Printf("VPN Server IP: %s\n", cfg.VpnServerIP)
	fmt.Printf("Is HTTPS Enabled: %t\n", cfg.IsHTTPS)
	fmt.Println("-------------------------------------------")

	// Setup router
	router := SetupRouter()

	// Start server
	addr := fmt.Sprintf(":%d", 8080) // Use a default port for now
	log.Printf("Server starting on %s", addr)
	if err := router.Run(addr); err != nil {
		log.Fatalf("Server failed to start: %v", err)
	}
}
