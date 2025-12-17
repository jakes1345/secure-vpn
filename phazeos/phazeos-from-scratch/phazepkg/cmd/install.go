package cmd

import (
	"fmt"
	"io"
	"os"
	"path/filepath"

	"github.com/phazeos/phazepkg/pkg/archive"
	"github.com/spf13/cobra"
)

var InstallCmd = &cobra.Command{
	Use:   "install [package.phz]",
	Short: "Install a package",
	Long:  `Installs a .phz package to the system root (or specified root).`,
	Args:  cobra.ExactArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		pkgFile := args[0]
		rootDir, _ := cmd.Flags().GetString("root")

		// 1. Validate input
		if _, err := os.Stat(pkgFile); os.IsNotExist(err) {
			fmt.Printf("Error: Package file not found: %s\n", pkgFile)
			os.Exit(1)
		}

		fmt.Printf("📦 Installing %s to %s...\n", pkgFile, rootDir)

		// 2. Extract to temp dir
		tempDir, err := os.MkdirTemp("", "phazepkg-install-*")
		if err != nil {
			fmt.Printf("Error creating temp dir: %v\n", err)
			os.Exit(1)
		}
		defer os.RemoveAll(tempDir) // Cleanup on exit

		if err := archive.Extract(pkgFile, tempDir); err != nil {
			fmt.Printf("❌ Install Failed (Extraction): %v\n", err)
			os.Exit(1)
		}

		// 3. Move files to root
		// TODO: Read metadata first for stricter checks

		dataDir := filepath.Join(tempDir, "data")
		if _, err := os.Stat(dataDir); os.IsNotExist(err) {
			// Some packages might be flat or follow different structure? Design said data/
			fmt.Println("Warning: No 'data' directory in package. Installing flat content?")
			dataDir = tempDir
		} else {
			// Using rsync locally or manual walk copy in Go
			// For simplicity in pure Go:
			err = copyDir(dataDir, rootDir)
			if err != nil {
				fmt.Printf("❌ Install Failed (Copy): %v\n", err)
				os.Exit(1)
			}
		}

		// TODO: Database registration

		fmt.Println("✅ Install Complete!")
	},
}

func init() {
	InstallCmd.Flags().String("root", "/", "Installation root directory")
}

// Simple recursive copy function
func copyDir(src, dst string) error {
	return filepath.Walk(src, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}

		relPath, err := filepath.Rel(src, path)
		if err != nil {
			return err
		}

		if relPath == "." {
			return nil
		}

		targetPath := filepath.Join(dst, relPath)

		if info.IsDir() {
			return os.MkdirAll(targetPath, info.Mode())
		}

		// Copy file
		srcFile, err := os.Open(path)
		if err != nil {
			return err
		}
		defer srcFile.Close()

		dstFile, err := os.OpenFile(targetPath, os.O_CREATE|os.O_WRONLY|os.O_TRUNC, info.Mode())
		if err != nil {
			return err
		}
		defer dstFile.Close()

		_, err = io.Copy(dstFile, srcFile)
		return err
	})
}
