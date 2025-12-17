package api

// PackageMetadata describes a PhazeOS package
type PackageMetadata struct {
	Name         string   `json:"name"`
	Version      string   `json:"version"`
	Description  string   `json:"description"`
	Arch         string   `json:"arch"`
	Dependencies []string `json:"dependencies"`
	Maintainer   string   `json:"maintainer"`
	License      string   `json:"license"`
}

// PackageIndex represents the repository index
type PackageIndex struct {
	Packages []PackageMetadata `json:"packages"`
	Updated  string            `json:"updated"` // ISO 8601 date
}
