# PhazePkg Design Document

## 1. Overview
`phazepkg` is the custom package manager for PhazeOS. It is designed to be:
- **Simple**: Easy to understand, maintain, and use.
- **Secure**: Built-in privacy checks and signing (future).
- **Fast**: Written in Go, using simple tar.zst archives.
- **Local-First**: Prioritizes local caching and building.

## 2. Package Format (`.phz`)
A PhazeOS package is a simple compressed archive file: `name-version-arch.phz`.
Under the hood, it is a `tar.zst` (Zstandard compressed tarball).

**Content Structure:**
```
/
├── metadata.json  # Package info (name, version, deps, maintainer)
├── install.sh     # (Optional) Post-install script
└── data/          # The actual files to extract to /
    ├── usr/
    │   └── bin/
    │       └── hello
    └── etc/
        └── hello.conf
```

## 3. Metadata Format (`metadata.json`)
```json
{
  "name": "nano",
  "version": "7.2",
  "description": "The Nano text editor",
  "arch": "x86_64",
  "dependencies": ["libc", "ncurses"],
  "maintainer": "Jack <jack@phazeos.org>",
  "license": "GPL-3.0"
}
```

## 4. Repository Structure
The remote (or local) repository is a simple static file server structure.
```
repo/
├── x86_64/
│   ├── index.json        # List of all available packages & metadata
│   ├── nano-7.2.phz
│   ├── vim-9.0.phz
│   └── ...
└── databases/
    └── core.db           # Sqlite or JSON db of package data
```

## 5. Components
1.  **CLI (`phazepkg`)**: The user-facing tool.
    *   `install <package>`: Downloads and extracts.
    *   `remove <package>`: Removes files tracked in local DB.
    *   `update`: Refreshes package lists.
    *   `upgrade`: Upgrades all installed packages.
    *   `build`: Creates a `.phz` from a build directory.
2.  **Local Database**: Tracks installed packages and their files.
    *   Location: `/var/lib/phazepkg/db/installed.json` (or BoltDB/SQLite).

## 6. Implementation Plan
- **Step 1: Scaffolding**: Setup Go project and directory structure.
- **Step 2: Core Library**: Implement struct definitions and metadata parsing.
- **Step 3: Archive Handling**: Implement `.phz` (tar.zst) creation and extraction.
- **Step 4: Database**: Implement local tracking of installed files.
- **Step 5: CLI**: Implement the command-line interface.

## 7. Build System Integration
We will move from raw shell scripts (like `22-build-phase2.sh`) to `phazepkg build` recipes.
Each "recipe" will be a folder with a `build.sh` and `metadata.json`.
`phazepkg` will run the build in a sane environment and package the output.
