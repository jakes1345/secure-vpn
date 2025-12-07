package utils

import (
	"testing"
)

func TestHashPassword(t *testing.T) {
	password := "securepassword123"
	hash, err := HashPassword(password)
	if err != nil {
		t.Fatalf("HashPassword failed: %v", err)
	}

	if !CheckPasswordHash(password, hash) {
		t.Errorf("CheckPasswordHash failed: password should match hash")
	}

	if CheckPasswordHash("wrongpassword", hash) {
		t.Errorf("CheckPasswordHash failed: wrong password should not match hash")
	}
}

func TestFormatBytes(t *testing.T) {
	tests := []struct {
		input    int64
		expected string
	}{
		{0, "0 B"},
		{512, "512 B"},
		{1024, "1.00 KB"},
		{1024 * 1024, "1.00 MB"},
		{1024 * 1024 * 1024, "1.00 GB"},
		{1536 * 1024 * 1024, "1.50 GB"},
		{1024 * 1024 * 1024 * 1024, "1.00 TB"},
		{1024 * 1024 * 1024 * 1024 * 1024, "1.00 PB"},
	}

	for _, test := range tests {
		result := FormatBytes(test.input)
		if result != test.expected {
			t.Errorf("FormatBytes(%d) got %s, want %s", test.input, result, test.expected)
		}
	}
}

func TestFormatDuration(t *testing.T) {
	tests := []struct {
		input    int
		expected string
	}{
		{0, ""}, // Go's time.Duration doesn't show 0s unless it's the only unit
		{59, "59s"},
		{60, "1m"},
		{3600, "1h"},
		{3661, "1h 1m"},
		{86400, "1d"},
		{90061, "1d 1h 1m"},
	}

	for _, test := range tests {
		result := FormatDuration(test.input)
		// Clean up trailing space for comparison
		if test.input > 0 && result[len(result)-1] == ' ' {
			result = result[:len(result)-1]
		}
		if result != test.expected {
			t.Errorf("FormatDuration(%d) got '%s', want '%s'", test.input, result, test.expected)
		}
	}
}
