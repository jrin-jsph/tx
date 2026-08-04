# MUX — Keyboard Input Multiplexer

MUX is a cross-platform, terminal-based keyboard input multiplexer. It allows one physical keyboard connected to a computer to control either the local machine or a paired remote computer over a secure local network connection.

## Key Features

- **Local & Remote Routing**: Seamlessly switch keyboard input between local OS and remote paired host.
- **Cross-Platform Support**: Supported configurations:
  - Linux Host → Linux Remote
  - Linux Host → Windows Remote
  - Windows Host → Linux Remote
- **Fail-Safe Fallback**: Automatic local fallback if remote connection or network drops.
- **Secure Pairing**: Cryptographically secure 6-character alphanumeric pairing codes with single-use, expiration, and rate-limiting.
- **TLS 1.3 Encryption**: Encrypted socket transport and monotonic sequence replay protection.
- **LAN Discovery**: Local network discovery (`mux devices`).
- **Terminal CLI**: Lightweight, modern developer-oriented console interface.

## Quick Start

### Installation

```bash
pip install -e .
```

### Basic Commands

```bash
# Display operational status matrix
mux status

# Host a MUX server and generate a 6-character pairing code
mux host [port]

# Connect to a remote MUX host (prompts for pairing code)
mux connect <ip> [port]

# Disconnect from active remote host and restore local control
mux disconnect

# Scan local network for MUX instances
mux devices

# Check system diagnostics & permissions
mux doctor

# Manage configuration settings
mux config show
mux config reset

# Switch active input target mode
mux switch local
mux switch remote

# Help
mux help
```

## Security & Architecture

- **Pairing**: Out-of-band 6-character alphanumeric code using Python's `secrets` module.
- **Transport**: Standard TLS socket encryption with length-prefixed protocol framing.
- **Isolation**: In `REMOTE` mode, Linux uses exclusive `EVIOCGRAB` grabbing; Windows uses `SendInput` and virtual key code injection.

## Documentation

- [Architecture Overview](docs/architecture.md)
- [Protocol Specification](docs/protocol.md)
- [Security Model](docs/security.md)
- [Development Guide](docs/development.md)

## License

MIT License. See [LICENSE](LICENSE) for details.
