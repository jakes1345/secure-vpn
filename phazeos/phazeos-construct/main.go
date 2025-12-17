package main

import (
	"fmt"
	"math"
	"os/exec"
	"time"

	rl "github.com/gen2brain/raylib-go/raylib"
)

// Constants
const (
	ScreenWidth  = 1920
	ScreenHeight = 1080
	Title        = "PHAZEOS CONSTRUCT - v2.0 [ARCADE]"
)

// State Machine
type GameState int

const (
	StateInit GameState = iota
	StateChoice
	StateArchitect
	StateSpeedrun
	StateInstall
	StateDone
)

var (
	currentState GameState = StateInit
	startTime    time.Time

	// Retro Effects
	crtShader  rl.Shader
	target     rl.RenderTexture2D
	frameCount int

	// Animation Vars
	gridOffset  float32
	typingSpeed int = 3 // Frames per char
)

// CRT Shader Code (Embedded GLSL 330)
const crtFragShader = `
#version 330

in vec2 fragTexCoord;
in vec4 fragColor;

out vec4 finalColor;

uniform sampler2D texture0;
uniform float time;

void main()
{
    vec2 uv = fragTexCoord;
    
    // Curvature (Fish-eye)
    vec2 d = uv - 0.5;
    float r = dot(d, d);
    uv = uv + d * (0.1 * r);
    
    // Scanlines
    float scanline = sin(uv.y * 800.0 + time * 5.0) * 0.04;
    
    // Chromatic Aberration (Color Split)
    float shift = 0.002;
    float r_col = texture(texture0, uv + vec2(-shift, 0.0)).r;
    float g_col = texture(texture0, uv).g;
    float b_col = texture(texture0, uv + vec2(shift, 0.0)).b;
    
    vec3 color = vec3(r_col, g_col, b_col);
    
    // Vignette
    float vig = 16.0 * uv.x * uv.y * (1.0 - uv.x) * (1.0 - uv.y);
    vig = pow(vig, 0.2);
    
    color -= scanline;
    color *= vig;
    
    // Black out of bounds (for curvature)
    if (uv.x < 0.0 || uv.x > 1.0 || uv.y < 0.0 || uv.y > 1.0)
        color = vec3(0.0);

    finalColor = vec4(color, 1.0);
}
`

func main() {
	rl.InitWindow(ScreenWidth, ScreenHeight, Title)
	rl.SetTargetFPS(60)
	rl.ToggleFullscreen()
	rl.SetMouseCursor(rl.MouseCursorCrosshair)

	// Load Retro Shader
	crtShader = rl.LoadShaderFromMemory("", crtFragShader)
	target = rl.LoadRenderTexture(ScreenWidth, ScreenHeight)

	startTime = time.Now()

	for !rl.WindowShouldClose() {
		// Update Logic
		frameCount++
		gridOffset += 1.0
		if gridOffset > 40.0 {
			gridOffset = 0
		}

		// Update Shader Uniforms
		timeSeconds := float32(rl.GetTime())
		locTime := rl.GetShaderLocation(crtShader, "time")
		rl.SetShaderValue(crtShader, locTime, []float32{timeSeconds}, rl.ShaderUniformFloat)

		// State Logic
		Update()

		// Draw to Texture (Low Res feeling)
		rl.BeginTextureMode(target)
		rl.ClearBackground(rl.Black)

		DrawRetroBackground()
		DrawInterface()

		rl.EndTextureMode()

		// Final Draw to Screen with Shader
		rl.BeginDrawing()
		rl.ClearBackground(rl.Black)
		rl.BeginShaderMode(crtShader)
		// Draw texture flipped Y
		source := rl.NewRectangle(0, 0, float32(target.Texture.Width), float32(-target.Texture.Height))
		dest := rl.NewRectangle(0, 0, float32(ScreenWidth), float32(ScreenHeight))
		rl.DrawTexturePro(target.Texture, source, dest, rl.Vector2{}, 0, rl.White)
		rl.EndShaderMode()

		// Draw FPS in corner (Retro yellow)
		rl.DrawText(fmt.Sprintf("FPS: %d", rl.GetFPS()), 20, 20, 20, rl.Yellow)
		rl.EndDrawing()
	}

	rl.UnloadRenderTexture(target)
	rl.UnloadShader(crtShader)
	rl.CloseWindow()
}

func Update() {
	switch currentState {
	case StateInit:
		if time.Since(startTime).Seconds() > 5 {
			currentState = StateChoice
		}
	case StateChoice:
		if rl.IsKeyPressed(rl.KeyA) {
			currentState = StateArchitect
		}
		if rl.IsKeyPressed(rl.KeyB) {
			currentState = StateSpeedrun
		}
	case StateArchitect:
		if rl.IsKeyPressed(rl.KeyEnter) {
			currentState = StateInstall
			startTime = time.Now()
			// Trigger Backend Install
			go func() {
				cmd := exec.Command("/usr/local/bin/phazeos-install-backend")
				cmd.Run()
				// For now we simulate
				time.Sleep(5 * time.Second)
			}()
		}
	case StateSpeedrun:
		currentState = StateInstall
		startTime = time.Now()
	case StateInstall:
		if time.Since(startTime).Seconds() > 5 {
			currentState = StateDone
		}
	}
}

func DrawRetroBackground() {
	// Cyber Grid - Tron Style
	cols := 20
	rows := 10
	spacing := 100

	// Perspective Horizon
	horizonY := 400

	// Draw Vertical Lines (fading to horizon)
	for i := -cols; i < cols; i++ {
		x := (ScreenWidth / 2) + (i * spacing * 2)
		// Simple perspective fake: lines converge to center
		topX := (ScreenWidth / 2) + int(float32(i*10)) // Converge

		rl.DrawLine(int32(topX), int32(horizonY), int32(x), ScreenHeight, rl.Fade(rl.Magenta, 0.4))
	}

	// Draw Horizontal Moving Lines
	for i := 0; i < rows; i++ {
		y := horizonY + (i * 60) + int(gridOffset)
		if y > ScreenHeight {
			y = horizonY
		}

		rl.DrawLine(0, int32(y), ScreenWidth, int32(y), rl.Fade(rl.Magenta, 0.5))
	}

	// Sun / Moon / Retro Circle
	rl.DrawCircleGradient(int32(ScreenWidth/2), int32(horizonY-50), 150, rl.Fade(rl.Orange, 0.8), rl.Fade(rl.DarkPurple, 0.0))
}

func DrawInterface() {
	// Blinking Cursor logic
	cursor := " "
	if (frameCount/30)%2 == 0 {
		cursor = "_"
	}

	switch currentState {
	case StateInit:
		DrawTypewriterText("SYSTEM DETECTED...", 100, 200, 40, rl.Green)
		if time.Since(startTime).Seconds() > 2 {
			DrawTypewriterText("INITIALIZING PHAZEOS CONSTRUCT...", 100, 260, 40, rl.Green)
		}
		if time.Since(startTime).Seconds() > 4 {
			rl.DrawText("PRESS ANY KEY TO JACK IN"+cursor, 100, 400, 30, rl.DarkGreen)
		}

	case StateChoice:
		rl.DrawText("SELECT PROTOCOL"+cursor, ScreenWidth/2-150, 100, 50, rl.White)

		// Path A Box
		rl.DrawRectangleLines(300, 300, 500, 600, rl.SkyBlue)
		rl.DrawText("THE ARCHITECT", 400, 350, 40, rl.SkyBlue)
		rl.DrawText("MANUAL BUILD", 400, 450, 30, rl.DarkGray)
		rl.DrawText("Customize Everything", 400, 500, 20, rl.Gray)
		rl.DrawText("[ PRESS A ]", 450, 800, 30, rl.White)

		// Path B Box
		rl.DrawRectangleLines(1120, 300, 500, 600, rl.Magenta)
		rl.DrawText("THE SPEEDRUN", 1220, 350, 40, rl.Magenta)
		rl.DrawText("AUTO INSTALL", 1220, 450, 30, rl.DarkGray)
		rl.DrawText("Max Performance", 1220, 500, 20, rl.Gray)
		rl.DrawText("[ PRESS B ]", 1270, 800, 30, rl.White)

	case StateArchitect:
		rl.DrawText("ARCHITECT MODE // CONSTRUCTING"+cursor, 50, 50, 30, rl.Green)
		// Draw simple vector shapes instead of textures
		rl.DrawRectangleLines(ScreenWidth/2-100, ScreenHeight/2-100, 200, 200, rl.Green)
		rl.DrawText("CORE", ScreenWidth/2-40, ScreenHeight/2-10, 30, rl.Green)

		rl.DrawText("Drag Modules (Coming Soon in v2.1)...", 50, ScreenHeight-100, 20, rl.Gray)

	case StateSpeedrun:
		// Matrix Rain Effect (Simple)
		for i := 0; i < 20; i++ {
			x := int32(i * 100)
			y := int32((frameCount * 5 * (i + 1)) % ScreenHeight)
			rl.DrawText(string(rune(33+i)), x, y, 30, rl.Fade(rl.Green, 0.5))
		}
		rl.DrawText("INSTALLING... "+fmt.Sprintf("%.0f%%", math.Min(float64(frameCount)/5.0, 100.0)), ScreenWidth/2-200, ScreenHeight/2, 60, rl.Green)
	}
}

// Helper to type text out
func DrawTypewriterText(text string, x, y, fontSize int, color rl.Color) {
	framesVisible := frameCount / typingSpeed
	if framesVisible > len(text) {
		framesVisible = len(text)
	}
	rl.DrawText(text[:framesVisible], int32(x), int32(y), int32(fontSize), color)
}
