"""
File locking utilities to prevent race conditions in JSON file operations
"""

import fcntl
import json
import time
import os
from pathlib import Path
from typing import Dict, Any, Optional
import threading

class FileLock:
    """Context manager for file locking"""
    
    def __init__(self, file_path: Path, timeout: int = 10):
        self.file_path = file_path
        self.timeout = timeout
        self.file_handle = None
        self.locked = False
    
    def __enter__(self):
        self.acquire()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()
    
    def acquire(self):
        """Acquire file lock with timeout"""
        start_time = time.time()
        while time.time() - start_time < self.timeout:
            try:
                # Open file in append mode for locking
                self.file_path.parent.mkdir(parents=True, exist_ok=True)
                self.file_handle = open(self.file_path, 'a')
                fcntl.flock(self.file_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                self.locked = True
                return True
            except (IOError, OSError):
                if self.file_handle:
                    self.file_handle.close()
                    self.file_handle = None
                time.sleep(0.1)  # Wait 100ms before retry
        
        raise TimeoutError(f"Could not acquire lock on {self.file_path} within {self.timeout} seconds")
    
    def release(self):
        """Release file lock"""
        if self.locked and self.file_handle:
            fcntl.flock(self.file_handle.fileno(), fcntl.LOCK_UN)
            self.file_handle.close()
            self.file_handle = None
            self.locked = False

def safe_json_read(file_path: Path, default: Any = None) -> Any:
    """
    Safely read JSON file with locking
    
    Args:
        file_path: Path to JSON file
        default: Default value if file doesn't exist
    
    Returns:
        Parsed JSON data or default
    """
    if not file_path.exists():
        return default if default is not None else {}
    
    try:
        with FileLock(file_path):
            with open(file_path, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return default if default is not None else {}

def safe_json_write(file_path: Path, data: Any, create_backup: bool = True):
    """
    Safely write JSON file with locking and atomic write
    
    Args:
        file_path: Path to JSON file
        data: Data to write
        create_backup: Whether to create backup before writing
    """
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create backup if requested
    if create_backup and file_path.exists():
        backup_path = file_path.with_suffix(f'.backup.{int(time.time())}')
        try:
            import shutil
            shutil.copy2(file_path, backup_path)
            # Keep only last 5 backups
            backups = sorted(file_path.parent.glob(f'{file_path.stem}.backup.*'))
            for old_backup in backups[:-5]:
                old_backup.unlink()
        except Exception as e:
            print(f"Warning: Could not create backup: {e}")
    
    # Write to temporary file first (atomic write)
    temp_path = file_path.with_suffix('.tmp')
    
    try:
        with FileLock(file_path):
            # Write to temp file
            with open(temp_path, 'w') as f:
                json.dump(data, f, indent=2)
                f.flush()
                os.fsync(f.fileno())  # Force write to disk
            
            # Atomic rename (works on Unix, Windows may need different approach)
            import os
            temp_path.replace(file_path)
    except Exception as e:
        # Clean up temp file on error
        if temp_path.exists():
            temp_path.unlink()
        raise Exception(f"Error writing {file_path}: {e}")

def safe_json_update(file_path: Path, update_func, default: Any = None):
    """
    Safely update JSON file with locking
    
    Args:
        file_path: Path to JSON file
        update_func: Function that takes current data and returns updated data
        default: Default value if file doesn't exist
    
    Returns:
        Updated data
    """
    with FileLock(file_path):
        # Read current data
        if file_path.exists():
            with open(file_path, 'r') as f:
                current_data = json.load(f)
        else:
            current_data = default if default is not None else {}
        
        # Update data
        updated_data = update_func(current_data)
        
        # Write back
        temp_path = file_path.with_suffix('.tmp')
        with open(temp_path, 'w') as f:
            json.dump(updated_data, f, indent=2)
            f.flush()
            import os
            os.fsync(f.fileno())
        
        # Atomic rename
        temp_path.replace(file_path)
        
        return updated_data

