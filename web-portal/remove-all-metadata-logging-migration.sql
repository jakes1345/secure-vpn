-- Migration: Remove all metadata logging and tracking
-- Run with: mysql -u phazevpn -p phazevpn < remove-all-metadata-logging-migration.sql

USE phazevpn;

-- Drop sessions table (not used, but exists in schema)
DROP TABLE IF EXISTS sessions;

-- Drop connection_history table (privacy violation)
DROP TABLE IF EXISTS connection_history;

-- Remove ip_address column from rate_limits (privacy violation)
-- First check if column exists
SET @exist := (SELECT COUNT(*) FROM information_schema.COLUMNS 
    WHERE TABLE_SCHEMA = 'phazevpn' 
    AND TABLE_NAME = 'rate_limits' 
    AND COLUMN_NAME = 'ip_address');

SET @sqlstmt := IF(@exist > 0, 
    'ALTER TABLE rate_limits DROP COLUMN ip_address',
    'SELECT "Column ip_address does not exist" AS message');

PREPARE stmt FROM @sqlstmt;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Add username column if it doesn't exist
SET @exist := (SELECT COUNT(*) FROM information_schema.COLUMNS 
    WHERE TABLE_SCHEMA = 'phazevpn' 
    AND TABLE_NAME = 'rate_limits' 
    AND COLUMN_NAME = 'username');

SET @sqlstmt := IF(@exist = 0, 
    'ALTER TABLE rate_limits ADD COLUMN username VARCHAR(100) NOT NULL AFTER id',
    'SELECT "Column username already exists" AS message');

PREPARE stmt FROM @sqlstmt;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Change primary key to (username, endpoint, window_start)
-- First drop old primary key
ALTER TABLE rate_limits DROP PRIMARY KEY;

-- Add new composite primary key
ALTER TABLE rate_limits ADD PRIMARY KEY (username, endpoint, window_start);

-- Truncate rate_limits to remove any IP-based entries
TRUNCATE TABLE rate_limits;

SELECT 'Migration complete - All metadata logging removed' AS status;
