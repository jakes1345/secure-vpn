package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"image/color"
	"io"
	"log"
	"net/http"
	"time"

	"fyne.io/fyne/v2"
	"fyne.io/fyne/v2/app"
	"fyne.io/fyne/v2/canvas"
	"fyne.io/fyne/v2/container"
	"fyne.io/fyne/v2/dialog"
	"fyne.io/fyne/v2/layout"
	"fyne.io/fyne/v2/theme"
	"fyne.io/fyne/v2/widget"

	"phazevpn-server/internal/client"
)

const (
	CURRENT_VERSION = "2.0.0"
	API_BASE_URL    = "https://phazevpn.com"
)

// Custom colors
var (
	PhazeColor  = color.NRGBA{R: 102, G: 126, B: 234, A: 255}
	CyanColor   = color.NRGBA{R: 0, G: 255, B: 136, A: 255}
	PurpleColor = color.NRGBA{R: 118, G: 75, B: 162, A: 255}
)

// API Response structures
type LoginResponse struct {
	Token    string `json:"token"`
	Username string `json:"username"`
	Error    string `json:"error"`
}

type VPNKeysResponse struct {
	Username  string `json:"username"`
	WireGuard struct {
		PrivateKey string `json:"private_key"`
		PublicKey  string `json:"public_key"`
		ClientIP   string `json:"client_ip"`
	} `json:"wireguard"`
	PhazeVPN struct {
		Key      string `json:"key"`
		ClientIP string `json:"client_ip"`
	} `json:"phazevpn"`
	Server struct {
		Address       string `json:"address"`
		WireGuardPort int    `json:"wireguard_port"`
		OpenVPNPort   int    `json:"openvpn_port"`
		PhazeVPNPort  int    `json:"phazevpn_port"`
	} `json:"server"`
}

// Login to API
func loginToAPI(username, password string) (*LoginResponse, error) {
	loginData := map[string]string{
		"username": username,
		"password": password,
	}

	jsonData, _ := json.Marshal(loginData)
	resp, err := http.Post(API_BASE_URL+"/api/login", "application/json", bytes.NewBuffer(jsonData))
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	var loginResp LoginResponse
	if err := json.NewDecoder(resp.Body).Decode(&loginResp); err != nil {
		return nil, err
	}

	if loginResp.Error != "" {
		return nil, fmt.Errorf(loginResp.Error)
	}

	return &loginResp, nil
}

// Fetch VPN keys from API
func fetchVPNKeys(token string) (*VPNKeysResponse, error) {
	req, _ := http.NewRequest("GET", API_BASE_URL+"/api/vpn/keys", nil)
	req.AddCookie(&http.Cookie{
		Name:  "session_token",
		Value: token,
	})

	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	var keys VPNKeysResponse
	if err := json.NewDecoder(resp.Body).Decode(&keys); err != nil {
		return nil, err
	}

	return &keys, nil
}

// Show login window
func showLoginWindow(a fyne.App) (*LoginResponse, error) {
	loginWin := a.NewWindow("PhazeVPN - Login")
	loginWin.Resize(fyne.NewSize(400, 300))
	loginWin.SetFixedSize(true)

	var loginResp *LoginResponse
	var loginErr error
	done := make(chan bool)

	// Header
	header := widget.NewLabel("⚡ PHAZE VPN")
	header.TextStyle = fyne.TextStyle{Bold: true}
	header.Alignment = fyne.TextAlignCenter

	subtitle := widget.NewLabel("Login to your account")
	subtitle.Alignment = fyne.TextAlignCenter

	// Input fields
	usernameEntry := widget.NewEntry()
	usernameEntry.SetPlaceHolder("Username")

	passwordEntry := widget.NewPasswordEntry()
	passwordEntry.SetPlaceHolder("Password")

	errorLabel := widget.NewLabel("")
	errorLabel.Alignment = fyne.TextAlignCenter
	errorLabel.TextStyle = fyne.TextStyle{Bold: true}

	// Login button
	loginBtn := widget.NewButton("Login", func() {})
	loginBtn.Importance = widget.HighImportance

	loginBtn.OnTapped = func() {
		username := usernameEntry.Text
		password := passwordEntry.Text

		if username == "" || password == "" {
			errorLabel.SetText("Please enter username and password")
			return
		}

		loginBtn.Disable()
		loginBtn.SetText("Logging in...")
		errorLabel.SetText("")

		go func() {
			resp, err := loginToAPI(username, password)

			fyne.Do(func() {
				if err != nil {
					errorLabel.SetText("Login failed: " + err.Error())
					loginBtn.Enable()
					loginBtn.SetText("Login")
				} else {
					loginResp = resp
					loginErr = nil
					loginWin.Close()
					done <- true
				}
			})
		}()
	}

	// Sign up link
	signupBtn := widget.NewButton("Don't have an account? Sign up on website", func() {
		// Open browser to signup page
		// For now just show message
		dialog.ShowInformation("Sign Up",
			"Please visit https://phazevpn.com/signup to create an account",
			loginWin)
	})
	signupBtn.Importance = widget.LowImportance

	content := container.NewVBox(
		layout.NewSpacer(),
		header,
		subtitle,
		layout.NewSpacer(),
		usernameEntry,
		passwordEntry,
		errorLabel,
		loginBtn,
		signupBtn,
		layout.NewSpacer(),
	)

	loginWin.SetContent(container.NewPadded(content))
	loginWin.ShowAndRun()

	return loginResp, loginErr
}

func main() {
	a := app.NewWithID("com.phazevpn.client")
	a.Settings().SetTheme(theme.DarkTheme())

	// Show login window first
	loginResp, err := showLoginWindow(a)
	if err != nil || loginResp == nil {
		log.Println("Login cancelled or failed")
		return
	}

	// Fetch VPN keys
	keys, err := fetchVPNKeys(loginResp.Token)
	if err != nil {
		log.Println("Failed to fetch VPN keys:", err)
		return
	}

	// Create main window
	w := a.NewWindow("PhazeVPN - " + loginResp.Username)
	w.Resize(fyne.NewSize(450, 700))
	w.SetFixedSize(true)

	// --- Header ---
	headerLabel := widget.NewLabel("⚡ PHAZE VPN")
	headerLabel.TextStyle = fyne.TextStyle{Bold: true, Monospace: true}
	headerLabel.Alignment = fyne.TextAlignCenter

	versionLabel := widget.NewLabel("v" + CURRENT_VERSION + " • " + loginResp.Username)
	versionLabel.Alignment = fyne.TextAlignCenter
	versionLabel.TextStyle = fyne.TextStyle{Italic: true}

	// --- Status ---
	statusDot := canvas.NewCircle(color.NRGBA{R: 255, G: 0, B: 0, A: 255})
	statusDot.Resize(fyne.NewSize(12, 12))

	statusLabel := widget.NewLabel("Disconnected")
	statusLabel.Alignment = fyne.TextAlignCenter
	statusLabel.TextStyle = fyne.TextStyle{Bold: true}

	statusContainer := container.NewHBox(
		layout.NewSpacer(),
		statusDot,
		statusLabel,
		layout.NewSpacer(),
	)

	// --- IP Display ---
	ipLabel := widget.NewLabel("Your IP: Fetching...")
	ipLabel.Alignment = fyne.TextAlignCenter

	vpnIPLabel := widget.NewLabel("VPN IP: Not Connected")
	vpnIPLabel.Alignment = fyne.TextAlignCenter

	// --- Connection Time ---
	timeLabel := widget.NewLabel("Duration: --:--:--")
	timeLabel.Alignment = fyne.TextAlignCenter

	// --- Stats ---
	downloadLabel := widget.NewLabelWithStyle("↓ 0.0 MB", fyne.TextAlignCenter, fyne.TextStyle{Bold: true})
	uploadLabel := widget.NewLabelWithStyle("↑ 0.0 MB", fyne.TextAlignCenter, fyne.TextStyle{Bold: true})

	statsContainer := container.NewGridWithColumns(2,
		container.NewVBox(widget.NewLabelWithStyle("DOWNLOAD", fyne.TextAlignCenter, fyne.TextStyle{}), downloadLabel),
		container.NewVBox(widget.NewLabelWithStyle("UPLOAD", fyne.TextAlignCenter, fyne.TextStyle{}), uploadLabel),
	)

	// --- Protocol Selection ---
	protocols := []string{"PhazeVPN (Recommended)", "WireGuard", "OpenVPN"}
	protocolSelect := widget.NewSelect(protocols, func(selected string) {
		log.Println("Selected protocol:", selected)
	})
	protocolSelect.SetSelected("PhazeVPN (Recommended)")

	// --- Connect Button ---
	var btnConnect *widget.Button
	var isConnected bool
	var vpnClient *client.PhazeVPNClient
	var connectTime time.Time

	btnConnect = widget.NewButton("⚡ CONNECT", func() {
		if isConnected {
			if vpnClient != nil {
				vpnClient.Disconnect()
				vpnClient = nil
			}
			isConnected = false
			btnConnect.SetText("⚡ CONNECT")
			btnConnect.Importance = widget.HighImportance
			statusLabel.SetText("Disconnected")
			statusDot.FillColor = color.NRGBA{R: 255, G: 0, B: 0, A: 255}
			statusDot.Refresh()
			vpnIPLabel.SetText("VPN IP: Not Connected")
			timeLabel.SetText("Duration: --:--:--")
			a.SendNotification(fyne.NewNotification("PhazeVPN", "Disconnected"))
			return
		}

		btnConnect.Disable()
		btnConnect.SetText("CONNECTING...")
		statusLabel.SetText("Handshaking...")
		statusDot.FillColor = color.NRGBA{R: 255, G: 165, B: 0, A: 255}
		statusDot.Refresh()

		go func() {
			// Use user's actual VPN credentials
			serverAddr := keys.Server.Address
			serverPort := keys.Server.PhazeVPNPort
			clientIP := keys.PhazeVPN.ClientIP
			vpnNetwork := "10.9.0.0/24"

			c, err := client.NewPhazeVPNClient(serverAddr, serverPort, vpnNetwork, clientIP)
			if err != nil {
				fyne.Do(func() {
					statusLabel.SetText("Error: " + err.Error())
					statusDot.FillColor = color.NRGBA{R: 255, G: 0, B: 0, A: 255}
					statusDot.Refresh()
					btnConnect.Enable()
					btnConnect.SetText("⚡ CONNECT")
				})
				return
			}

			if err := c.Connect(); err != nil {
				fyne.Do(func() {
					statusLabel.SetText("Connection Failed")
					statusDot.FillColor = color.NRGBA{R: 255, G: 0, B: 0, A: 255}
					statusDot.Refresh()
					btnConnect.Enable()
					btnConnect.SetText("⚡ CONNECT")
				})
				return
			}

			vpnClient = c
			isConnected = true
			connectTime = time.Now()

			fyne.Do(func() {
				btnConnect.Enable()
				btnConnect.SetText("🔌 DISCONNECT")
				btnConnect.Importance = widget.DangerImportance
				statusLabel.SetText("Connected • Secured")
				statusDot.FillColor = CyanColor
				statusDot.Refresh()
				vpnIPLabel.SetText(fmt.Sprintf("VPN IP: %s", clientIP))
				a.SendNotification(fyne.NewNotification("PhazeVPN", "🔒 Secure Connection Established"))
			})

			// Stats & Time Loop
			go func() {
				ticker := time.NewTicker(1 * time.Second)
				for isConnected {
					<-ticker.C
					duration := time.Since(connectTime)
					fyne.Do(func() {
						timeLabel.SetText(fmt.Sprintf("Duration: %02d:%02d:%02d",
							int(duration.Hours()),
							int(duration.Minutes())%60,
							int(duration.Seconds())%60))
					})
				}
			}()
		}()
	})
	btnConnect.Importance = widget.HighImportance

	// Settings Button
	btnSettings := widget.NewButtonWithIcon("", theme.SettingsIcon(), func() {
		dialog.ShowInformation("Account",
			fmt.Sprintf("👤 Logged in as: %s\n\n"+
				"🔑 VPN Keys: Configured\n"+
				"🌐 Server: %s\n"+
				"⚡ Protocol: PhazeVPN",
				loginResp.Username, keys.Server.Address), w)
	})

	// --- Layout ---
	hero := container.NewVBox(
		layout.NewSpacer(),
		headerLabel,
		versionLabel,
		layout.NewSpacer(),
		widget.NewCard("", "", container.NewPadded(
			container.NewVBox(
				statusContainer,
				widget.NewSeparator(),
				ipLabel,
				vpnIPLabel,
				timeLabel,
				widget.NewSeparator(),
				statsContainer,
			),
		)),
	)

	controls := container.NewVBox(
		widget.NewLabel("Protocol"),
		protocolSelect,
		layout.NewSpacer(),
		btnConnect,
	)

	content := container.NewBorder(
		nil,
		container.NewHBox(layout.NewSpacer(), btnSettings),
		nil,
		nil,
		container.NewVBox(
			hero,
			layout.NewSpacer(),
			controls,
		),
	)

	w.SetContent(container.NewPadded(content))

	// Get real IP on startup
	go func() {
		resp, err := http.Get("https://api.ipify.org?format=text")
		if err == nil {
			defer resp.Body.Close()
			ip, _ := io.ReadAll(resp.Body)
			fyne.Do(func() {
				ipLabel.SetText(fmt.Sprintf("Your IP: %s", string(ip)))
			})
		}
	}()

	w.ShowAndRun()
}
