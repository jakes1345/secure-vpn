package api

import (
	"encoding/json"
	"io/ioutil"
	"net/http"
	"strings"
	"time"
)

type Email struct {
	From    string `json:"from"`
	Subject string `json:"subject"`
	Date    string `json:"date"`
	Unread  bool   `json:"unread"`
}

type EmailStats struct {
	Unread int     `json:"unread"`
	Total  int     `json:"total"`
	Recent []Email `json:"recent"`
}

// GetEmails returns REAL emails from web portal API
func GetEmails(w http.ResponseWriter, r *http.Request) {
	stats := EmailStats{
		Unread: 0,
		Total:  0,
		Recent: []Email{},
	}

	// Try to fetch from web portal API
	client := &http.Client{
		Timeout: 5 * time.Second,
	}

	// Try multiple endpoints
	endpoints := []string{
		"https://phazevpn.com/api/emails",
		"https://51.91.121.135/api/emails",
		"http://localhost:5000/api/emails",
	}

	var resp *http.Response
	var err error

	for _, endpoint := range endpoints {
		resp, err = client.Get(endpoint)
		if err == nil && resp.StatusCode == 200 {
			break
		}
	}

	if err != nil || resp == nil {
		// Fallback: return empty stats
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(stats)
		return
	}

	defer resp.Body.Close()

	body, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(stats)
		return
	}

	// Parse response
	if err := json.Unmarshal(body, &stats); err != nil {
		// Try alternative format
		var emails []Email
		if err := json.Unmarshal(body, &emails); err == nil {
			stats.Recent = emails
			stats.Total = len(emails)

			// Count unread
			for _, email := range emails {
				if email.Unread {
					stats.Unread++
				}
			}
		}
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(stats)
}

// SendEmail sends an email via web portal API
func SendEmail(w http.ResponseWriter, r *http.Request) {
	if r.Method != "POST" {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	var req struct {
		To      string `json:"to"`
		Subject string `json:"subject"`
		Body    string `json:"body"`
	}

	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	// Forward to web portal API
	client := &http.Client{
		Timeout: 10 * time.Second,
	}

	jsonData, _ := json.Marshal(req)

	endpoints := []string{
		"https://phazevpn.com/api/send_email",
		"https://51.91.121.135/api/send_email",
	}

	var resp *http.Response
	var err error

	for _, endpoint := range endpoints {
		resp, err = client.Post(endpoint, "application/json", strings.NewReader(string(jsonData)))
		if err == nil && resp.StatusCode == 200 {
			break
		}
	}

	if err != nil || resp == nil {
		http.Error(w, "Failed to send email", http.StatusInternalServerError)
		return
	}

	defer resp.Body.Close()

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{
		"status":  "sent",
		"message": "Email sent successfully",
	})
}
