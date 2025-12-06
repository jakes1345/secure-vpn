-- Remove IP tracking for complete privacy
-- Run this on your database to remove all IP address storage

-- Remove IP column from connection_history (ignore error if doesn't exist)
SET @exist := (SELECT COUNT(*) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = 'phazevpn' AND TABLE_NAME = 'connection_history' AND COLUMN_NAME = 'ip_address');
SET @sqlstmt := IF(@exist > 0, 'ALTER TABLE connection_history DROP COLUMN ip_address', 'SELECT "Column ip_address does not exist"');
PREPARE stmt FROM @sqlstmt;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Remove IP column from rate_limits (ignore error if doesn't exist)
SET @exist := (SELECT COUNT(*) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = 'phazevpn' AND TABLE_NAME = 'rate_limits' AND COLUMN_NAME = 'ip_address');
SET @sqlstmt := IF(@exist > 0, 'ALTER TABLE rate_limits DROP COLUMN ip_address', 'SELECT "Column ip_address does not exist"');
PREPARE stmt FROM @sqlstmt;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Add username column to rate_limits if it doesn't exist
SET @exist := (SELECT COUNT(*) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = 'phazevpn' AND TABLE_NAME = 'rate_limits' AND COLUMN_NAME = 'username');
SET @sqlstmt := IF(@exist = 0, 'ALTER TABLE rate_limits ADD COLUMN username VARCHAR(255)', 'SELECT "Column username already exists"');
PREPARE stmt FROM @sqlstmt;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Delete all existing connection history (contains IPs)
TRUNCATE TABLE connection_history;

-- Delete all existing rate limits (contains IPs)
TRUNCATE TABLE rate_limits;
