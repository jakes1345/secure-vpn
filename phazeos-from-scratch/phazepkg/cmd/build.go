package cmd

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"

	"github.com/phazeos/phazepkg/pkg/api"
	"github.com/phazeos/phazepkg/pkg/archive"
	"github.com/spf13/cobra"
)

var BuildCmd = &cobra.Command{
	Use:   "build [directory]",
	Short: "Build a package from a directory",
	Long:  `Creates a .phz package archive from the specified directory. The directory must contain a valid metadata.json file.`,
	Args:  cobra.ExactArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		sourceDir := args[0]

		// 1. Read metadata
		metaPath := filepath.Join(sourceDir, "metadata.json")
		if _, err := os.Stat(metaPath); os.IsNotExist(err) {
			fmt.Printf("Error: metadata.json not found in %s\n", sourceDir)
			os.Exit(1)
		}

		metaFile, err := os.ReadFile(metaPath)
		if err != nil {
			fmt.Printf("Error reading metadata: %v\n", err)
			os.Exit(1)
		}

		var meta api.PackageMetadata
		if err := json.Unmarshal(metaFile, &meta); err != nil {
			fmt.Printf("Error parsing metadata.json: %v\n", err)
			os.Exit(1)
		}

		// Validation (Basic)
		if meta.Name == "" || meta.Version == "" || meta.Arch == "" {
			fmt.Println("Error: Invalid metadata. Name, Version, and Arch are required.")
			os.Exit(1)
		}

		// 2. Determine output filename
		outName := fmt.Sprintf("%s-%s-%s.phz", meta.Name, meta.Version, meta.Arch)

		fmt.Printf("📦 Building Package: %s v%s (%s)\n", meta.Name, meta.Version, meta.Arch)
		fmt.Printf("📂 Source: %s\n", sourceDir)
		fmt.Printf("💾 Output: %s\n", outName)

		// 3. Compress
		if err := archive.Compress(sourceDir, outName); err != nil {
			fmt.Printf("❌ Build Failed: %v\n", err)
			os.Exit(1)
		}

		fmt.Println("✅ Build Complete!")
	},
}
