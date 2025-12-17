package stats

import (
	"fmt"
	"sync"
	"time"
)

// TrafficStats tracks bandwidth usage
type TrafficStats struct {
	bytesReceived   uint64
	bytesSent       uint64
	packetsReceived uint64
	packetsSent     uint64
	startTime       time.Time
	mutex           sync.RWMutex
}

// NewTrafficStats creates a new stats tracker
func NewTrafficStats() *TrafficStats {
	return &TrafficStats{
		startTime: time.Now(),
	}
}

// AddReceived records received bytes
func (ts *TrafficStats) AddReceived(bytes int) {
	ts.mutex.Lock()
	ts.bytesReceived += uint64(bytes)
	ts.packetsReceived++
	ts.mutex.Unlock()
}

// AddSent records sent bytes
func (ts *TrafficStats) AddSent(bytes int) {
	ts.mutex.Lock()
	ts.bytesSent += uint64(bytes)
	ts.packetsSent++
	ts.mutex.Unlock()
}

// GetStats returns current statistics
func (ts *TrafficStats) GetStats() (received, sent uint64, duration time.Duration) {
	ts.mutex.RLock()
	defer ts.mutex.RUnlock()
	return ts.bytesReceived, ts.bytesSent, time.Since(ts.startTime)
}

// GetRates returns current transfer rates in bytes/second
func (ts *TrafficStats) GetRates() (downloadRate, uploadRate float64) {
	ts.mutex.RLock()
	defer ts.mutex.RUnlock()

	duration := time.Since(ts.startTime).Seconds()
	if duration == 0 {
		return 0, 0
	}

	downloadRate = float64(ts.bytesReceived) / duration
	uploadRate = float64(ts.bytesSent) / duration
	return
}

// GetPacketCounts returns packet counts
func (ts *TrafficStats) GetPacketCounts() (received, sent uint64) {
	ts.mutex.RLock()
	defer ts.mutex.RUnlock()
	return ts.packetsReceived, ts.packetsSent
}

// Reset resets all statistics
func (ts *TrafficStats) Reset() {
	ts.mutex.Lock()
	ts.bytesReceived = 0
	ts.bytesSent = 0
	ts.packetsReceived = 0
	ts.packetsSent = 0
	ts.startTime = time.Now()
	ts.mutex.Unlock()
}

// FormatBytes converts bytes to human-readable format
func FormatBytes(bytes uint64) string {
	const unit = 1024
	if bytes < unit {
		return fmt.Sprintf("%d B", bytes)
	}
	div, exp := uint64(unit), 0
	for n := bytes / unit; n >= unit; n /= unit {
		div *= unit
		exp++
	}
	return fmt.Sprintf("%.1f %cB", float64(bytes)/float64(div), "KMGTPE"[exp])
}

// FormatRate converts bytes/sec to human-readable format
func FormatRate(bytesPerSec float64) string {
	const unit = 1024.0
	if bytesPerSec < unit {
		return fmt.Sprintf("%.0f B/s", bytesPerSec)
	}
	div, exp := unit, 0
	for n := bytesPerSec / unit; n >= unit; n /= unit {
		div *= unit
		exp++
	}
	return fmt.Sprintf("%.1f %cB/s", bytesPerSec/div, "KMGTPE"[exp])
}
