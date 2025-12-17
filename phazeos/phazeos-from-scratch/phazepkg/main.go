package main

import (
	"fmt"
	"os"

	"github.com/phazeos/phazepkg/cmd"
	"github.com/spf13/cobra"
)

var rootCmd = &cobra.Command{
	Use:   "phazepkg",
	Short: "PhazeOS Package Manager",
	Long:  `Fast, secure, and privacy-focused package manager for PhazeOS.`,
}

func init() {
	rootCmd.AddCommand(cmd.BuildCmd)
	rootCmd.AddCommand(cmd.InstallCmd)
}

func main() {
	if err := rootCmd.Execute(); err != nil {
		fmt.Println(err)
		os.Exit(1)
	}
}
