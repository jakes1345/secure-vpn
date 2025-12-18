#!/bin/bash
#===============================================================================
# PhazeOS QEMU Debug Script
# Comprehensive debugging for ISO boot testing
# Captures: serial console, kernel logs, QEMU monitor, and more
#===============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ISO_DIR="${SCRIPT_DIR}/out"
LOG_DIR="${SCRIPT_DIR}/debug-logs"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Default settings
MEMORY="4096"
CPUS="2"
ENABLE_KVM="yes"
DEBUG_LEVEL="full"  # minimal, standard, full
HEADLESS="no"

# Log files
SERIAL_LOG="${LOG_DIR}/serial_${TIMESTAMP}.log"
QEMU_LOG="${LOG_DIR}/qemu_${TIMESTAMP}.log"
BOOT_ANALYSIS="${LOG_DIR}/boot_analysis_${TIMESTAMP}.txt"

#===============================================================================
# Helper Functions
#===============================================================================

print_header() {
    echo -e "\n${CYAN}╔══════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║${NC} ${BOLD}$1${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════════════════════════════════╝${NC}\n"
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

#===============================================================================
# Find ISO
#===============================================================================

find_iso() {
    if [[ -n "$1" && -f "$1" ]]; then
        ISO_PATH="$1"
    else
        # Find the most recent ISO
        ISO_PATH=$(find "${ISO_DIR}" -name "*.iso" -type f -printf '%T@ %p\n' 2>/dev/null | sort -rn | head -1 | cut -d' ' -f2-)
    fi

    if [[ -z "$ISO_PATH" || ! -f "$ISO_PATH" ]]; then
        print_error "No ISO found! Build the ISO first."
        exit 1
    fi

    echo "$ISO_PATH"
}

#===============================================================================
# Setup
#===============================================================================

setup_environment() {
    print_header "PhazeOS QEMU Debug Environment"

    # Create log directory
    mkdir -p "${LOG_DIR}"

    # Check for QEMU
    if ! command -v qemu-system-x86_64 &> /dev/null; then
        print_error "qemu-system-x86_64 not found! Install QEMU first."
        exit 1
    fi

    # Check KVM support
    if [[ "$ENABLE_KVM" == "yes" ]]; then
        if [[ ! -e /dev/kvm ]]; then
            print_warning "/dev/kvm not found - KVM disabled"
            ENABLE_KVM="no"
        elif [[ ! -r /dev/kvm || ! -w /dev/kvm ]]; then
            print_warning "No access to /dev/kvm - trying with sudo or disabling KVM"
            if sudo test -r /dev/kvm 2>/dev/null; then
                print_info "Will use sudo for KVM access"
                USE_SUDO="yes"
            else
                ENABLE_KVM="no"
            fi
        fi
    fi

    print_info "Log directory: ${LOG_DIR}"
    print_info "Timestamp: ${TIMESTAMP}"
}

#===============================================================================
# Build QEMU Command
#===============================================================================

build_qemu_command() {
    local iso="$1"
    local cmd=""

    # Base QEMU command
    if [[ "$USE_SUDO" == "yes" ]]; then
        cmd="sudo "
    fi
    cmd+="qemu-system-x86_64"

    # KVM acceleration
    if [[ "$ENABLE_KVM" == "yes" ]]; then
        cmd+=" -enable-kvm"
        cmd+=" -cpu host"
    else
        cmd+=" -cpu max"
    fi

    # Memory and CPUs
    cmd+=" -m ${MEMORY}"
    cmd+=" -smp ${CPUS}"

    # Boot from CD-ROM
    cmd+=" -cdrom \"${iso}\""
    cmd+=" -boot d"

    # Display (unless headless)
    if [[ "$HEADLESS" == "yes" ]]; then
        cmd+=" -display none"
    else
        cmd+=" -display gtk"
    fi

    #---------------------------------------------------------------------------
    # DEBUG OPTIONS - The magic sauce!
    #---------------------------------------------------------------------------

    # Serial console - captures ALL kernel/boot messages
    cmd+=" -serial file:${SERIAL_LOG}"

    # Alternative: multiplexed serial for interactive + logging
    # cmd+=" -serial mon:stdio"

    # Enable QEMU monitor on telnet for control/inspection
    cmd+=" -monitor telnet:127.0.0.1:55555,server,nowait"

    # Debug logging (writes to stderr, we redirect to file)
    cmd+=" -d guest_errors,unimp"

    # BIOS/UEFI debugging
    cmd+=" -debugcon file:${LOG_DIR}/debugcon_${TIMESTAMP}.log"
    cmd+=" -global isa-debugcon.iobase=0x402"

    # Network with user-mode (works without root)
    cmd+=" -netdev user,id=net0,hostfwd=tcp::2222-:22"
    cmd+=" -device virtio-net-pci,netdev=net0"

    # Use virtio for better performance
    cmd+=" -device virtio-vga"

    # Add a virtual disk for persistence testing (optional)
    # cmd+=" -drive file=${LOG_DIR}/test-disk.qcow2,format=qcow2,if=virtio"

    # USB support
    cmd+=" -usb"
    cmd+=" -device usb-tablet"

    # RTC (real-time clock) - helps with timing issues
    cmd+=" -rtc base=localtime"

    # Machine type
    cmd+=" -machine q35"

    echo "$cmd"
}

#===============================================================================
# Monitor Log in Real-Time
#===============================================================================

#===============================================================================
# Monitor Boot Status (Enhanced)
#===============================================================================

monitor_boot_status() {
    local log_file="$1"
    local pid="$2"
    local ssh_port="2222"
    local start_time=$(date +%s)
    local timeout=300 # 5 minutes

    print_header "Monitoring Boot Status..."
    print_info "1. Watching serial log: ${log_file}"
    print_info "2. Polling SSH port: localhost:${ssh_port}"
    echo ""

    # Wait for log file
    while [[ ! -f "$log_file" ]]; do sleep 0.5; done

    local boot_detected="no"
    
    while kill -0 "$pid" 2>/dev/null; do
        local current_time=$(date +%s)
        local elapsed=$((current_time - start_time))

        # Check timeout
        if [[ $elapsed -gt $timeout ]]; then
            print_error "Boot timed out after ${timeout} seconds."
            break
        fi

        # 1. Check for specific success messages in log (if any appear)
        if grep -q "PhazeOS login:" "$log_file"; then
            print_success "Boot confirmed via Serial Log!"
            boot_detected="yes"
            break
        fi

        # 2. Check for SSH port (The "Pulse" Check)
        # Using /dev/tcp bash feature to check port without nc/telnet dependency if possible, 
        # but nc is more reliable for timeouts.
        if command -v nc &>/dev/null; then
            if nc -z -w 1 localhost "$ssh_port" 2>/dev/null; then
                print_success "Boot confirmed via Network (SSH Port Open)!"
                print_info "System is UP after ${elapsed} seconds."
                boot_detected="yes"
                break
            fi
        else
            # Fallback to bash tcp
            (echo > /dev/tcp/localhost/$ssh_port) >/dev/null 2>&1
            if [[ $? -eq 0 ]]; then
                print_success "Boot confirmed via Network (SSH Port Open)!"
                boot_detected="yes"
                break
            fi
        fi

        sleep 2
    done

    if [[ "$boot_detected" == "yes" ]]; then
        echo ""
        print_info "The ISO works! You can interact with it in the QEMU window."
        print_info "Trying to connect via SSH..."
        echo "ssh -p $ssh_port root@localhost"
        echo ""
    fi
}

#===============================================================================
# Quick Commands (for scripting)
#===============================================================================

quick_run() {
    setup_environment
    local iso=$(find_iso "$1")
    local cmd=$(build_qemu_command "$iso")

    print_info "Quick run - ISO: ${iso}"
    print_info "Monitor: telnet 127.0.0.1 55555"
    echo ""

    # Run in background
    print_info "Starting QEMU..."
    eval "$cmd" 2>"${QEMU_LOG}" &
    QEMU_PID=$!

    # Monitor the boot
    monitor_boot_status "${SERIAL_LOG}" "${QEMU_PID}"
    
    # Wait for user to explicitly kill QEMU or script
    wait $QEMU_PID 2>/dev/null
}

#===============================================================================
# Main
#===============================================================================

usage() {
    echo "Usage: $0 [command] [iso-path]"
    echo ""
    echo "Commands:"
    echo "  run       - Quick run with full debugging (default)"
    echo "  menu      - Interactive menu"
    echo "  headless  - Run without GUI"
    echo "  analyze   - Analyze existing log"
    echo "  logs      - View available logs"
    echo "  help      - Show this help"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Run latest ISO with debugging"
    echo "  $0 run /path/to/custom.iso           # Run specific ISO"
    echo "  $0 menu                               # Show interactive menu"
    echo "  $0 analyze                            # Analyze last boot log"
}

main() {
    case "${1:-run}" in
        run|start)
            quick_run "$2"
            ;;
        menu)
            show_menu
            ;;
        headless)
            HEADLESS="yes"
            quick_run "$2"
            ;;
        analyze)
            setup_environment
            analyze_existing
            ;;
        logs|view)
            setup_environment
            view_logs
            ;;
        clean)
            setup_environment
            clean_logs
            ;;
        help|-h|--help)
            usage
            ;;
        *)
            # Assume it's an ISO path
            if [[ -f "$1" ]]; then
                quick_run "$1"
            else
                usage
                exit 1
            fi
            ;;
    esac
}

# Run main
main "$@"
