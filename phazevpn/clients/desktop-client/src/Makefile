.PHONY: build clean test run install

# Build the server
build:
	go build -o phazevpn-server-go -ldflags "-s -w" .

# Build for Linux (cross-compile)
build-linux:
	GOOS=linux GOARCH=amd64 go build -o phazevpn-server-go-linux -ldflags "-s -w" .

# Clean build artifacts
clean:
	rm -f phazevpn-server-go phazevpn-server-go-linux

# Run tests
test:
	go test ./...

# Run the server (requires root for TUN)
run: build
	sudo ./phazevpn-server-go

# Install dependencies
install:
	go mod download
	go mod tidy

# Format code
fmt:
	go fmt ./...

# Lint code
lint:
	golangci-lint run ./...

