#!/usr/bin/env python3
import time
import sys
import os
import random
import subprocess

# Colors
GREEN = '\033[92m'
RED = '\033[91m'
BLUE = '\033[94m'
CYAN = '\033[96m'
YELLOW = '\033[93m'
BOLD = '\033[1m'
RESET = '\033[0m'

def type_text(text, speed=0.03, color=GREEN):
    """Effect to type text like a terminal"""
    sys.stdout.write(color)
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(speed + random.uniform(-0.01, 0.01))
    sys.stdout.write(RESET + '\n')

def loading_bar(label, duration=2):
    """Hacker-style loading bar"""
    frames = ["[=         ]", "[==        ]", "[===       ]", "[====      ]", "[=====     ]", 
              "[======    ]", "[=======   ]", "[========  ]", "[========= ]", "[==========]"]
    
    sys.stdout.write(f"\r{CYAN}{label}... {RESET}")
    for _ in range(duration * 5):
        for frame in frames:
            sys.stdout.write(f"\r{CYAN}{label}... {frame}{RESET}")
            sys.stdout.flush()
            time.sleep(0.05)
    print(f"\r{GREEN}{label}... [COMPLETE]          {RESET}")

def clear_screen():
    os.system('clear')

def banner():
    clear_screen()
    print(f"{BOLD}{GREEN}")
    print(r"""
  ____  _   _    _     _____ _____    ___  ____  
 |  _ \| | | |  / \   |__  /| ____|  / _ \/ ___| 
 | |_) | |_| | / _ \    / / |  _|   | | | \___ \ 
 |  __/|  _  |/ ___ \  / /_ | |___  | |_| |___) |
 |_|   |_| |_/_/   \_\/____||_____|  \___/|____/ 
                                                 
    INITIALIZATION PROTOCOL v1.0.4
    SECURE TERMINAL ACCESS
    """)
    print(f"{RESET}")

def run_step(step_name, command=None):
    type_text(f"[SYSTEM] Initiating {step_name}...", speed=0.01)
    if command:
        # In a real install, we would run the command
        # subprocess.run(command, shell=True)
        time.sleep(1)
    loading_bar(f"Processing {step_name}", duration=1)
    type_text(f"[SUCCESS] {step_name} Verified.", speed=0.005)

def main():
    banner()
    time.sleep(1)
    
    type_text("ESTABLISHING SECURE CONNECTION...", speed=0.05)
    time.sleep(0.5)
    type_text("VERIFYING HARDWARE INTEGRITY...", speed=0.02)
    time.sleep(0.5)
    
    # 1. Identity
    print("\n")
    type_text("Identity Verification Required.", color=YELLOW)
    username = input(f"{BOLD}{GREEN}ENTER CODENAME > {RESET}")
    
    type_text(f"Welcome, Agent {username}.", speed=0.05)
    time.sleep(1)
    
    # 2. Disk Selection (Simulated mainly for visual now)
    print("\n")
    type_text("SCANNING STORAGE ARRAYS...", speed=0.02)
    # lsblk simulation
    print(f"{BLUE}")
    print("DEVICE     SIZE    TYPE")
    print("nvme0n1    1024G   SSD  [PRIMARY]")
    print("sda        2000G   HDD  [BACKUP]")
    print(f"{RESET}")
    
    target = input(f"{BOLD}{GREEN}SELECT TARGET DEVICE (e.g. nvme0n1) > {RESET}")
    
    print("\n")
    type_text(f"WARNING: TARGET {target} WILL BE WIPED.", color=RED)
    confirm = input(f"{BOLD}{RED}CONFIRM DELETION PROTOCOL? (YES/NO) > {RESET}")
    
    if confirm.lower() != 'yes':
        type_text("ABORTING...", color=RED)
        sys.exit(1)
        
    # 3. Installation Flow
    clear_screen()
    banner()
    
    print(f"\n{BOLD}BEGINNING SYSTEM INJECTION...{RESET}\n")
    
    steps = [
        "Formatting Drive (BTRFS Encrypted)",
        "Mounting Subvolumes (@, @home, @log)",
        "Injecting Core Kernel (Linux-Zen)",
        "Deploying PhazeVPN Deamon",
        "Configuring 'Glass Wall' Firewall",
        "Installing PhazeBrowser",
        "Compiling Cyberpunk Assets",
        "Securing Bootloader"
    ]
    
    for step in steps:
        run_step(step)
        time.sleep(0.5)
        
    print("\n")
    type_text("SYSTEM INJECTION COMPLETE.", speed=0.02)
    type_text("REMOVING TRACES...", speed=0.05)
    
    print("\n")
    print(f"{BOLD}{GREEN}=========================================={RESET}")
    print(f"{BOLD}{GREEN}   SYSTEM READY. REBOOTING IN 3 SECONDS   {RESET}")
    print(f"{BOLD}{GREEN}=========================================={RESET}")
    
    time.sleep(3)
    # reboot

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[!] FORCED INTERRUPT. SYSTEM HALTED.")
