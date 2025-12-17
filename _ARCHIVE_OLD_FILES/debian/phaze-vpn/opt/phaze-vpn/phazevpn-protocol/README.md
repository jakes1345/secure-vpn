# PhazeVPN Protocol - Custom VPN Implementation

## Overview
PhazeVPN Protocol is a completely custom VPN solution built from scratch, independent of OpenVPN, WireGuard, or any other existing VPN software. This is our own proprietary implementation.

## Architecture

### Protocol Stack
```
┌─────────────────────────────────────┐
│   Application Layer (Your Apps)      │
├─────────────────────────────────────┤
│   TUN Interface (Virtual Network)    │
├─────────────────────────────────────┤
│   PhazeVPN Protocol Layer           │
│   - Packet Encryption/Decryption     │
│   - Key Exchange                     │
│   - Authentication                   │
│   - Session Management               │
├─────────────────────────────────────┤
│   Transport Layer (UDP/TCP)         │
├─────────────────────────────────────┤
│   Network Layer (IP)                 │
└─────────────────────────────────────┘
```

### Key Features
- **Custom Protocol**: Proprietary packet format and encryption
- **Zero Dependencies**: No OpenVPN, WireGuard, or other VPN software
- **Modern Cryptography**: ChaCha20-Poly1305, AES-256-GCM
- **Perfect Forward Secrecy**: Ephemeral key exchange
- **Kill Switch**: Built-in network isolation
- **DNS Leak Protection**: All DNS through VPN
- **Multi-Platform**: Python-based (works on Linux, Windows, macOS)

## Protocol Specification

### Packet Format
```
[Header (16 bytes)] [Encrypted Payload] [Auth Tag (16 bytes)]
```

### Header Structure
- Magic Number (4 bytes): 0x50 0x48 0x41 0x5A ("PHAZ")
- Version (1 byte): Protocol version
- Type (1 byte): Packet type (DATA, HANDSHAKE, KEEPALIVE, etc.)
- Sequence (4 bytes): Packet sequence number
- Session ID (4 bytes): Session identifier
- Length (2 bytes): Payload length

### Encryption
- **Cipher**: ChaCha20-Poly1305 (primary), AES-256-GCM (fallback)
- **Key Exchange**: ECDH with X25519 (Curve25519)
- **Key Derivation**: HKDF-SHA256
- **Nonce**: 12-byte random per packet

### Authentication
- Username/Password + Certificate-based
- Session tokens for reconnection
- Server certificate verification

## Components

1. **phazevpn-server.py**: Custom VPN server
2. **phazevpn-client.py**: Custom VPN client
3. **protocol.py**: Protocol implementation
4. **crypto.py**: Cryptographic functions
5. **tun_manager.py**: TUN interface management
6. **key_exchange.py**: Key exchange protocol

## Installation

```bash
# Server
sudo python3 phazevpn-server.py

# Client
python3 phazevpn-client.py
```

## Port
Default port: **51820** (different from OpenVPN's 1194)

## Security
- Military-grade encryption
- Perfect forward secrecy
- Zero-knowledge architecture
- No logging of user traffic
- Kill switch enabled by default

