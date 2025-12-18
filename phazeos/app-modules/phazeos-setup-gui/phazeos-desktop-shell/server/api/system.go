package api

import (
	"encoding/json"
	"io/ioutil"
	"net/http"
	"os/exec"
	"strconv"
	"strings"
	"time"
)

type SystemInfo struct {
	Hostname    string    `json:"hostname"`
	Uptime      string    `json:"uptime"`
	CPUUsage    string    `json:"cpu_usage"`
	MemoryUsage string    `json:"memory_usage"`
	DiskUsage   string    `json:"disk_usage"`
	Processes   int       `json:"processes"`
	LoadAvg     string    `json:"load_avg"`
	Timestamp   time.Time `json:"timestamp"`
}

// GetSystemInfo returns REAL system statistics
func GetSystemInfo(w http.ResponseWriter, r *http.Request) {
	info := SystemInfo{
		Hostname:    getHostname(),
		Uptime:      getRealUptime(),
		CPUUsage:    getRealCPUUsage(),
		MemoryUsage: getRealMemoryUsage(),
		DiskUsage:   getRealDiskUsage(),
		Processes:   getProcessCount(),
		LoadAvg:     getLoadAverage(),
		Timestamp:   time.Now(),
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(info)
}

func getHostname() string {
	cmd := exec.Command("hostname")
	output, err := cmd.Output()
	if err != nil {
		return "phazeos"
	}
	return strings.TrimSpace(string(output))
}

func getRealUptime() string {
	cmd := exec.Command("uptime", "-p")
	output, err := cmd.Output()
	if err != nil {
		return "Unknown"
	}
	return strings.TrimSpace(string(output))
}

func getRealCPUUsage() string {
	// Read /proc/stat twice with 100ms delay for accurate measurement
	stat1 := readCPUStat()
	time.Sleep(100 * time.Millisecond)
	stat2 := readCPUStat()

	if stat1 == nil || stat2 == nil {
		return "0%"
	}

	total1 := stat1["user"] + stat1["nice"] + stat1["system"] + stat1["idle"] + stat1["iowait"]
	total2 := stat2["user"] + stat2["nice"] + stat2["system"] + stat2["idle"] + stat2["iowait"]

	idle1 := stat1["idle"] + stat1["iowait"]
	idle2 := stat2["idle"] + stat2["iowait"]

	totalDelta := total2 - total1
	idleDelta := idle2 - idle1

	if totalDelta == 0 {
		return "0%"
	}

	usage := 100.0 * (float64(totalDelta-idleDelta) / float64(totalDelta))
	return strconv.FormatFloat(usage, 'f', 1, 64) + "%"
}

func readCPUStat() map[string]int64 {
	data, err := ioutil.ReadFile("/proc/stat")
	if err != nil {
		return nil
	}

	lines := strings.Split(string(data), "\n")
	for _, line := range lines {
		if strings.HasPrefix(line, "cpu ") {
			fields := strings.Fields(line)
			if len(fields) >= 6 {
				user, _ := strconv.ParseInt(fields[1], 10, 64)
				nice, _ := strconv.ParseInt(fields[2], 10, 64)
				system, _ := strconv.ParseInt(fields[3], 10, 64)
				idle, _ := strconv.ParseInt(fields[4], 10, 64)
				iowait, _ := strconv.ParseInt(fields[5], 10, 64)

				return map[string]int64{
					"user":   user,
					"nice":   nice,
					"system": system,
					"idle":   idle,
					"iowait": iowait,
				}
			}
		}
	}

	return nil
}

func getRealMemoryUsage() string {
	// Read /proc/meminfo
	data, err := ioutil.ReadFile("/proc/meminfo")
	if err != nil {
		return "Unknown"
	}

	lines := strings.Split(string(data), "\n")

	var total, available int64

	for _, line := range lines {
		if strings.HasPrefix(line, "MemTotal:") {
			fields := strings.Fields(line)
			if len(fields) >= 2 {
				total, _ = strconv.ParseInt(fields[1], 10, 64)
			}
		}
		if strings.HasPrefix(line, "MemAvailable:") {
			fields := strings.Fields(line)
			if len(fields) >= 2 {
				available, _ = strconv.ParseInt(fields[1], 10, 64)
			}
		}
	}

	if total == 0 {
		return "Unknown"
	}

	used := total - available
	usedGB := float64(used) / 1024 / 1024
	totalGB := float64(total) / 1024 / 1024

	return strconv.FormatFloat(usedGB, 'f', 1, 64) + " GB / " +
		strconv.FormatFloat(totalGB, 'f', 1, 64) + " GB"
}

func getRealDiskUsage() string {
	cmd := exec.Command("df", "-h", "/")
	output, err := cmd.Output()
	if err != nil {
		return "Unknown"
	}

	lines := strings.Split(string(output), "\n")
	if len(lines) > 1 {
		fields := strings.Fields(lines[1])
		if len(fields) >= 5 {
			return fields[4] // Usage percentage
		}
	}

	return "0%"
}

func getProcessCount() int {
	files, err := ioutil.ReadDir("/proc")
	if err != nil {
		return 0
	}

	count := 0
	for _, f := range files {
		if f.IsDir() {
			if _, err := strconv.Atoi(f.Name()); err == nil {
				count++
			}
		}
	}

	return count
}

func getLoadAverage() string {
	data, err := ioutil.ReadFile("/proc/loadavg")
	if err != nil {
		return "Unknown"
	}

	fields := strings.Fields(string(data))
	if len(fields) >= 3 {
		return fields[0] + " " + fields[1] + " " + fields[2]
	}

	return "Unknown"
}
