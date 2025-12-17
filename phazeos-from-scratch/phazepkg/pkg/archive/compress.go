package archive

import (
	"archive/tar"
	"fmt"
	"io"
	"os"
	"path/filepath"

	"github.com/klauspost/compress/zstd"
)

// Compress creates a .phz (tar.zst) archive from a source directory
func Compress(sourceDir, destFile string) error {
	// Create the output file
	outFile, err := os.Create(destFile)
	if err != nil {
		return fmt.Errorf("failed to create output file: %w", err)
	}
	defer outFile.Close()

	// Create Zstd writer
	zstdWriter, err := zstd.NewWriter(outFile)
	if err != nil {
		return fmt.Errorf("failed to create zstd writer: %w", err)
	}
	defer zstdWriter.Close()

	// Create Tar writer
	tarWriter := tar.NewWriter(zstdWriter)
	defer tarWriter.Close()

	// Walk the directory
	return filepath.Walk(sourceDir, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}

		// Create header
		header, err := tar.FileInfoHeader(info, info.Name())
		if err != nil {
			return err
		}

		// Update header name to be relative to sourceDir
		relPath, err := filepath.Rel(sourceDir, path)
		if err != nil {
			return err
		}

		// Use forward slashes for tar compatibility
		header.Name = filepath.ToSlash(relPath)

		if info.IsDir() {
			header.Name += "/"
		}

		// Write header
		if err := tarWriter.WriteHeader(header); err != nil {
			return err
		}

		// If it's a directory, just header is enough
		if info.IsDir() {
			return nil
		}

		// Write file content
		file, err := os.Open(path)
		if err != nil {
			return err
		}
		defer file.Close()

		_, err = io.Copy(tarWriter, file)
		return err
	})
}
