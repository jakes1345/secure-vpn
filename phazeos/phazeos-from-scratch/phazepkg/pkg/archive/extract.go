package archive

import (
	"archive/tar"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strings"

	"github.com/klauspost/compress/zstd"
)

// Extract decompresses a .phz (tar.zst) archive to a destination directory
func Extract(phzFile, destDir string) error {
	// Open the archive
	inFile, err := os.Open(phzFile)
	if err != nil {
		return fmt.Errorf("failed to open archive: %w", err)
	}
	defer inFile.Close()

	// Create Zstd reader
	zstdReader, err := zstd.NewReader(inFile)
	if err != nil {
		return fmt.Errorf("failed to create zstd reader: %w", err)
	}
	defer zstdReader.Close()

	// Create Tar reader
	tarReader := tar.NewReader(zstdReader)

	// Iterate through files
	for {
		header, err := tarReader.Next()
		if err == io.EOF {
			break // End of archive
		}
		if err != nil {
			return err
		}

		// Security: Prevent Zip Slip (.. in paths)
		target := filepath.Join(destDir, header.Name)
		if !isChild(destDir, target) {
			return fmt.Errorf("illegal file path in archive: %s", header.Name)
		}

		switch header.Typeflag {
		case tar.TypeDir:
			if err := os.MkdirAll(target, 0755); err != nil {
				return err
			}
		case tar.TypeReg:
			// Ensure parent dir exists
			if err := os.MkdirAll(filepath.Dir(target), 0755); err != nil {
				return err
			}

			// Create file
			outFile, err := os.OpenFile(target, os.O_CREATE|os.O_RDWR, os.FileMode(header.Mode))
			if err != nil {
				return err
			}

			// Copy content
			if _, err := io.Copy(outFile, tarReader); err != nil {
				outFile.Close()
				return err
			}
			outFile.Close()
		default:
			// Ignore other types (symlinks, etc. for now, or implement TODO)
			// TODO: Implement Symlink support
			fmt.Printf("Warning: Skipping unsupported type for %s\n", header.Name)
		}
	}

	return nil
}

// isChild checks if child path is actually inside parent path to prevent path traversal
func isChild(parent, child string) bool {
	rel, err := filepath.Rel(parent, child)
	if err != nil {
		return false
	}
	return !strings.HasPrefix(rel, ".."+string(os.PathSeparator)) && rel != ".."
}
