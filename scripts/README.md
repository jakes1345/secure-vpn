# Scripts Directory

This directory contains all utility, setup, deployment, and maintenance scripts organized by purpose.

## Directory Structure

### `setup/`
Setup and installation scripts
- `setup-*.py` / `setup-*.sh` - Initial setup scripts
- `auto-setup*.py` / `auto-setup*.sh` - Automated setup
- `complete-setup.py` - Complete setup automation
- `install.sh` - Main installation script

### `deploy/`
Deployment and synchronization scripts
- `deploy-*.py` / `deploy-*.sh` - Deployment scripts
- `DEPLOY-*.sh` - Deployment automation
- `sync-*.py` / `sync-*.sh` - File synchronization
- `SYNC-*.sh` - Sync automation

### `check/`
Verification and check scripts
- `check-*.py` / `check-*.sh` - Various checks
- `CHECK-*.py` / `CHECK-*.sh` - Check automation
- `verify-*.py` - Verification scripts
- `final-verify-*.py` - Final verification

### `build/`
Build scripts for all platforms
- `build-*.py` / `build-*.sh` - Build scripts
- `build-*.bat` - Windows build scripts
- `BUILD-*.bat` - Windows build automation

### `connect/`
Connection scripts
- `connect-*.sh` - VPS connection scripts
- `connect-*.py` - Connection automation

### `maintenance/`
Cleanup and optimization scripts
- `cleanup-*.py` / `cleanup-*.sh` - Cleanup scripts
- `optimize-*.py` / `optimize-*.sh` - Optimization scripts
- `update-*.py` / `update-*.sh` - Update scripts
- `aggressive-disk-cleanup.py` - Disk cleanup

### `utils/`
Utility scripts
- `add-*.py` / `add-*.sh` - Add/configure utilities
- `create-*.py` - Creation utilities
- `get-*.py` / `get-*.sh` - Retrieval utilities
- `finalize-*.py` - Finalization utilities

### `windows/`
Windows-specific scripts
- `*.bat` - Windows batch files
- Windows-only utilities

## Usage

Scripts are organized by purpose. To find a script:

1. Determine the script's purpose (setup, deploy, check, etc.)
2. Look in the corresponding directory
3. Scripts maintain their original names for easy identification

## Migration Notes

Scripts were moved from the root directory to maintain a clean project structure.
If you have scripts that reference these files, update paths from:
- `./setup-*.sh` → `scripts/setup/setup-*.sh`
- `./deploy-*.py` → `scripts/deploy/deploy-*.py`
- etc.

## Adding New Scripts

When adding new scripts:
1. Place them in the appropriate directory based on purpose
2. Follow naming conventions (`purpose-description.ext`)
3. Make scripts executable: `chmod +x script.sh`
4. Update this README if adding a new category
