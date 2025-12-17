package database

import (
	"database/sql"
	"encoding/json"
	"fmt"
	"log"
	"os"

	_ "github.com/go-sql-driver/mysql"
)

var DB *sql.DB

type Config struct {
	Host     string `json:"host"`
	User     string `json:"user"`
	Password string `json:"password"`
	Database string `json:"database"`
	Port     int    `json:"port"`
}

func Init() error {
	// Load config
	configFile := os.Getenv("DB_CONFIG")
	if configFile == "" {
		configFile = "db_config.json"
	}

	data, err := os.ReadFile(configFile)
	if err != nil {
		return fmt.Errorf("failed to read db config: %w", err)
	}

	var config Config
	if err := json.Unmarshal(data, &config); err != nil {
		return fmt.Errorf("failed to parse db config: %w", err)
	}

	// Build DSN
	dsn := fmt.Sprintf("%s:%s@tcp(%s:%d)/%s?parseTime=true&charset=utf8mb4",
		config.User,
		config.Password,
		config.Host,
		config.Port,
		config.Database,
	)

	// Connect
	db, err := sql.Open("mysql", dsn)
	if err != nil {
		return fmt.Errorf("failed to open database: %w", err)
	}

	// Test connection
	if err := db.Ping(); err != nil {
		return fmt.Errorf("failed to ping database: %w", err)
	}

	// Set connection pool settings
	db.SetMaxOpenConns(25)
	db.SetMaxIdleConns(5)
	db.SetConnMaxLifetime(5 * 60) // 5 minutes

	DB = db
	log.Println("✅ Database connected successfully")
	return nil
}

func Close() error {
	if DB != nil {
		return DB.Close()
	}
	return nil
}
