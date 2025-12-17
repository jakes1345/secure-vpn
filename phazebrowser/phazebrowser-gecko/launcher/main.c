#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/types.h>
#include <ifaddrs.h>
#include <net/if.h>
#include <libgen.h>
#include <limits.h>

// Function to check if VPN interface exists (tun* or wg*)
int check_vpn() {
    struct ifaddrs *ifaddr, *ifa;
    int vpn_found = 0;

    if (getifaddrs(&ifaddr) == -1) {
        perror("getifaddrs");
        return 0; // Fail safe or fail secure? Let's say fail secure (block)
    }

    for (ifa = ifaddr; ifa != NULL; ifa = ifa->ifa_next) {
        if (ifa->ifa_addr == NULL)
            continue;

        // Check for tun or wg interfaces
        if (strncmp(ifa->ifa_name, "tun", 3) == 0 || 
            strncmp(ifa->ifa_name, "wg", 2) == 0) {
            vpn_found = 1;
            break;
        }
    }

    freeifaddrs(ifaddr);
    return vpn_found;
}

// Function to show error dialog (simplest way without heavy deps is Zenity/Kdialog invoke)
void show_error(const char *message) {
    // Try Zenity (GTK)
    char cmd[1024];
    snprintf(cmd, sizeof(cmd), "zenity --error --text='%s' --title='PhazeBrowser Security' --width=400 2>/dev/null", message);
    if (system(cmd) != 0) {
        // Try Kdialog (KDE)
        snprintf(cmd, sizeof(cmd), "kdialog --error '%s' --title='PhazeBrowser Security' 2>/dev/null", message);
        if (system(cmd) != 0) {
            // Fallback to stderr
            fprintf(stderr, "SECURITY ERROR: %s\n", message);
        }
    }
}

int main(int argc, char *argv[]) {
    // 1. VPN Check
    // NOTE: For 'Dev Mode', we warn but allow. Uncomment failure logic for Prod.
    if (!check_vpn()) {
        // PROD:
        // show_error("VPN connection required!\n\nAccess blocked.");
        // return 1;
        
        // DEV:
        fprintf(stderr, "WARNING: VPN not detected. Launching in DEV MODE.\n");
    }

    // 2. Setup Paths
    char exe_path[PATH_MAX];
    ssize_t len = readlink("/proc/self/exe", exe_path, sizeof(exe_path) - 1);
    if (len == -1) {
        perror("readlink");
        return 1;
    }
    exe_path[len] = '\0';
    
    char *dir = dirname(exe_path);
    char ld_path[4096];
    char bin_path[PATH_MAX];
    
    // Construct paths
    snprintf(bin_path, sizeof(bin_path), "%s/firefox-bin", dir);
    
    // Get existing LD_LIBRARY_PATH
    char *current_ld = getenv("LD_LIBRARY_PATH");
    if (current_ld) {
        snprintf(ld_path, sizeof(ld_path), "%s:%s", dir, current_ld);
    } else {
        snprintf(ld_path, sizeof(ld_path), "%s", dir);
    }

    // 3. Set Environment
    setenv("LD_LIBRARY_PATH", ld_path, 1);
    setenv("MOZ_APP_NAME", "PhazeBrowser", 1);
    setenv("MOZ_APP_REMOTINGNAME", "PhazeBrowser", 1);
    setenv("GTK_THEME", "Adwaita:dark", 0); // Don't overwrite if set

    // 4. Config Arguments
    // We need to construct a new argv array
    // argv[0] = bin_path
    // argv[1..n] = original args
    // argv[n+1] = "--name"
    // argv[n+2] = "PhazeBrowser"
    // argv[n+3] = "--class"
    // argv[n+4] = "PhazeBrowser"
    // NULL
    
    int new_argc = argc + 4;
    char **new_argv = malloc(sizeof(char *) * (new_argc + 1));
    
    new_argv[0] = bin_path;
    for (int i = 1; i < argc; i++) {
        new_argv[i] = argv[i];
    }
    new_argv[argc] = "--name";
    new_argv[argc+1] = "PhazeBrowser";
    new_argv[argc+2] = "--class";
    new_argv[argc+3] = "PhazeBrowser";
    new_argv[argc+4] = NULL;

    printf("Starting Native PhazeBrowser...\n");
    printf("Binary: %s\n", bin_path);

    // 5. Execute
    execv(bin_path, new_argv);

    // If we get here, exec failed
    perror("execv failed");
    return 1;
}
