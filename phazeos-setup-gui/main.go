package main

import (
	"time"

	rl "github.com/gen2brain/raylib-go/raylib"
)

// Constants
const (
	ScreenWidth  = 1920
	ScreenHeight = 1080
	Title        = "PHAZEOS LINK - SETUP WIZARD"
)

// Setup States
type SetupState int

const (
	StateWelcome SetupState = iota
	StateUser
	StateWifi
	StateTheme
	StateFinalizing
	StateComplete
)

var (
	currentState SetupState = StateWelcome
	startTime    time.Time

	// Retro Effects
	crtShader  rl.Shader
	target     rl.RenderTexture2D
	frameCount int
	gridOffset float32

	// Input Vars
	userName string = ""
	wifiSSID string = "PhazeNet_5G"

	// Theme Selection
	selectedTheme int = 0 // 0: Cyberpunk, 1: Void, 2: Retro
)

// (Reusing CRT Shader from Installer for consistency)
const crtFragShader = `
#version 330
in vec2 fragTexCoord;
in vec4 fragColor;
out vec4 finalColor;
uniform sampler2D texture0;
uniform float time;
void main() {
    vec2 uv = fragTexCoord;
    vec2 d = uv - 0.5;
    float r = dot(d, d);
    uv = uv + d * (0.05 * r); // Less curvature for text readability
    float scanline = sin(uv.y * 800.0 + time * 5.0) * 0.04;
    float shift = 0.001;
    float r_col = texture(texture0, uv + vec2(-shift, 0.0)).r;
    float g_col = texture(texture0, uv).g;
    float b_col = texture(texture0, uv + vec2(shift, 0.0)).b;
    vec3 color = vec3(r_col, g_col, b_col);
    float vig = 16.0 * uv.x * uv.y * (1.0 - uv.x) * (1.0 - uv.y);
    vig = pow(vig, 0.2);
    color -= scanline;
    color *= vig;
    if (uv.x < 0.0 || uv.x > 1.0 || uv.y < 0.0 || uv.y > 1.0) color = vec3(0.0);
    finalColor = vec4(color, 1.0);
}
`

func main() {
	rl.InitWindow(ScreenWidth, ScreenHeight, Title)
	rl.SetTargetFPS(60)
	rl.ToggleFullscreen()
	rl.SetMouseCursor(rl.MouseCursorIBeam)

	crtShader = rl.LoadShaderFromMemory("", crtFragShader)
	target = rl.LoadRenderTexture(ScreenWidth, ScreenHeight)

	startTime = time.Now()

	for !rl.WindowShouldClose() {
		frameCount++
		gridOffset += 0.5
		if gridOffset > 40.0 {
			gridOffset = 0
		}

		timeSeconds := float32(rl.GetTime())
		locTime := rl.GetShaderLocation(crtShader, "time")
		rl.SetShaderValue(crtShader, locTime, []float32{timeSeconds}, rl.ShaderUniformFloat)

		HandleInput()

		rl.BeginTextureMode(target)
		rl.ClearBackground(rl.Black)
		DrawBackground()
		DrawUI()
		rl.EndTextureMode()

		rl.BeginDrawing()
		rl.ClearBackground(rl.Black)
		rl.BeginShaderMode(crtShader)
		source := rl.NewRectangle(0, 0, float32(target.Texture.Width), float32(-target.Texture.Height))
		dest := rl.NewRectangle(0, 0, float32(ScreenWidth), float32(ScreenHeight))
		rl.DrawTexturePro(target.Texture, source, dest, rl.Vector2{}, 0, rl.White)
		rl.EndShaderMode()
		rl.EndDrawing()
	}

	rl.UnloadRenderTexture(target)
	rl.UnloadShader(crtShader)
	rl.CloseWindow()
}

func HandleInput() {
	// Simple State Navigation
	if rl.IsKeyPressed(rl.KeyEnter) {
		if currentState < StateComplete {
			currentState++
		} else {
			rl.CloseWindow() // Exit when done
		}
	}

	// Capture text input for User step
	if currentState == StateUser {
		key := rl.GetCharPressed()
		for key > 0 {
			if (key >= 32) && (key <= 125) && (len(userName) < 12) {
				userName += string(key)
			}
			key = rl.GetCharPressed()
		}
		if rl.IsKeyPressed(rl.KeyBackspace) && len(userName) > 0 {
			userName = userName[:len(userName)-1]
		}
	}

	// Theme Selection
	if currentState == StateTheme {
		if rl.IsKeyPressed(rl.KeyLeft) {
			selectedTheme--
		}
		if rl.IsKeyPressed(rl.KeyRight) {
			selectedTheme++
		}
		if selectedTheme < 0 {
			selectedTheme = 2
		}
		if selectedTheme > 2 {
			selectedTheme = 0
		}
	}
}

func DrawBackground() {
	// Hexagon Grid for Setup (Different from Installer)
	color := rl.Fade(rl.DarkBlue, 0.3)
	for y := 0; y < ScreenHeight; y += 100 {
		for x := 0; x < ScreenWidth; x += 100 {
			rl.DrawPolyLines(rl.NewVector2(float32(x), float32(y)+gridOffset), 6, 50, 0, color)
		}
	}
}

func DrawUI() {
	// Header
	rl.DrawText("PHAZEOS LINK // CONFIGURATION", 50, 50, 30, rl.SkyBlue)

	cursor := "_"
	if (frameCount/30)%2 == 0 {
		cursor = " "
	}

	switch currentState {
	case StateWelcome:
		DrawCenteredText("SYSTEM ONLINE.", -100, 60, rl.Green)
		DrawCenteredText("Let's configure your identity.", 0, 30, rl.White)
		DrawCenteredText("[ PRESS ENTER TO BEGIN ]", 200, 20, rl.Gray)

	case StateUser:
		DrawCenteredText("IDENTITY", -200, 50, rl.SkyBlue)
		DrawCenteredText("ENTER USERNAME:", -50, 30, rl.White)

		// Input Box
		boxX := ScreenWidth/2 - 200
		rl.DrawRectangleLines(int32(boxX), ScreenHeight/2, 400, 60, rl.SkyBlue)
		rl.DrawText(userName+cursor, int32(boxX)+20, ScreenHeight/2+15, 30, rl.Green)

	case StateWifi:
		DrawCenteredText("UPLINK", -200, 50, rl.SkyBlue)
		rl.DrawText("SCANNING AIRWAVES...", int32(ScreenWidth/2-150), ScreenHeight/2-50, 30, rl.Gray)

		// Fake list
		rl.DrawText("> "+wifiSSID+" (Secured)", int32(ScreenWidth/2-200), ScreenHeight/2+20, 30, rl.Green)
		rl.DrawText("  FBI_Surveillance_Van", int32(ScreenWidth/2-200), ScreenHeight/2+70, 30, rl.DarkGray)
		rl.DrawText("  Free_WiFi", int32(ScreenWidth/2-200), ScreenHeight/2+120, 30, rl.DarkGray)

		DrawCenteredText("[ ENTER TO CONNECT ]", 300, 20, rl.Gray)

	case StateTheme:
		DrawCenteredText("VISUAL INTERFACE", -250, 50, rl.SkyBlue)

		themes := []string{"CYBERPUNK", "VOID", "RETRO"}
		colors := []rl.Color{rl.Magenta, rl.Black, rl.Orange}

		// Draw Carousel
		current := themes[selectedTheme]
		DrawCenteredText("<  "+current+"  >", 0, 60, colors[selectedTheme])

		if selectedTheme == 0 {
			DrawCenteredText("Neon aesthetics. High contrast.", 100, 20, rl.Gray)
		}
		if selectedTheme == 1 {
			DrawCenteredText("Minimalist. Distraction free.", 100, 20, rl.Gray)
		}
		if selectedTheme == 2 {
			DrawCenteredText("CRT Warmth. 1982 Style.", 100, 20, rl.Gray)
		}

	case StateFinalizing:
		DrawCenteredText("APPLYING CONFIGURATION...", 0, 40, rl.Green)
		// Loading Bar
		width := (frameCount * 2) % 600
		rl.DrawRectangle(ScreenWidth/2-300, ScreenHeight/2+50, int32(width), 20, rl.Green)
		rl.DrawRectangleLines(ScreenWidth/2-300, ScreenHeight/2+50, 600, 20, rl.DarkGreen)

		if width >= 580 {
			currentState = StateComplete
		}

	case StateComplete:
		DrawCenteredText("SETUP COMPLETE.", 0, 60, rl.Green)
		DrawCenteredText("Welcome to PhazeOS.", 100, 40, rl.White)
	}
}

func DrawCenteredText(text string, yOffset int, fontSize int, color rl.Color) {
	width := rl.MeasureText(text, int32(fontSize))
	rl.DrawText(text, int32(ScreenWidth/2)-width/2, int32(ScreenHeight/2+yOffset), int32(fontSize), color)
}
