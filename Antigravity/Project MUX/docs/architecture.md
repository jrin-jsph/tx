# MUX System Architecture

## Component Separation

MUX enforces strict isolation between component layers:

1. **CLI / Presentation Layer (`mux.cli`)**: Modern developer CLI interface built with clean ANSI theme styling, color toggles, and fallback rendering.
2. **Core Routing & State Machine (`mux.core`)**: Pure Python state machine managing target mode (`LOCAL` vs `REMOTE`) and connection states (`DISCONNECTED`, `PAIRING`, `CONNECTED_LOCAL`, `CONNECTED_REMOTE`, `FAILSAFE`, `ERROR`).
3. **Platform Layer (`mux.platform`)**: OS detection and permission diagnostics for Linux distribution parsing and Windows OS version detection.
4. **Input Capture & Injection (`mux.input`)**:
   - Linux: `LinuxInputCapturer` reading `/dev/input/eventX` via `evdev` or binary struct parsing with `EVIOCGRAB` grab isolation; `LinuxUInputInjector` injecting synthetic events.
   - Windows: `WindowsInputInjector` injecting synthetic keys via Win32 `SendInput` API; `WindowsInputCapturer` for input streaming.
5. **Security Layer (`mux.security`)**: Cryptographic pairing manager (`secrets`-based 6-character codes), TLS 1.3 certificate fingerprinting, and rate limiting.
6. **Network Layer (`mux.network`)**: Length-prefixed TCP socket framing, TLS transport (`Connection`), `MUXServer`, `MUXClient`, and UDP LAN `ServiceDiscovery`.
7. **Configuration Layer (`mux.config`)**: `ConfigManager` managing settings stored in OS-appropriate directories (`~/.config/mux/config.json` or `%APPDATA%\mux\config.json`).
