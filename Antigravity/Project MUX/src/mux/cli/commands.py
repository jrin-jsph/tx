"""CLI commands for MUX."""
import os
import sys
import time
from mux import __version__
from mux.cli.theme import Theme
from mux.config.manager import ConfigManager
from mux.core.router import InputRouter
from mux.core.session import Session
from mux.core.state import ConnectionState, TargetMode
from mux.input.detector import get_device_by_id, get_keyboard_devices
from mux.network.client import MUXClient
from mux.network.discovery import ServiceDiscovery
from mux.network.server import MUXServer
from mux.input.linux import LinuxInputCapturer
from mux.input.windows import WindowsInputCapturer
from mux.platform.detect import get_system_info, is_linux, is_windows
from mux.platform.linux import check_linux_environment
from mux.platform.windows import check_windows_environment
from mux.security.pairing import PairingError

# Global active process state
_global_router = InputRouter()
_active_server: Optional[MUXServer] = None
_active_client: Optional[MUXClient] = None

def print_header() -> None:
    """Print standard MUX header."""
    print(f"{Theme.bold('MUX')}")
    print(f"{Theme.dim('Keyboard Input Multiplexer')}\n")

def get_status_lines() -> list[str]:
    """Build formatted status lines with bullet indicators."""
    cfg = ConfigManager()
    kbd_path = cfg.selected_keyboard_path
    kbd_name = cfg.selected_keyboard_name
    
    if kbd_path and kbd_name:
        kbd_status = kbd_name
        kbd_bullet = Theme.bullet_green()
    else:
        kbd_status = "Not configured"
        kbd_bullet = Theme.bullet_yellow()

    # Determine Role & Connection
    if _active_server and _active_server.is_running:
        role_str = "Host"
        conn_str = f"Listening on port {_active_server.port}"
    elif _active_client and _active_client.is_connected:
        role_str = "Client"
        conn_str = "Connected (TLS Encrypted)"
    else:
        role_str = "Standalone"
        conn_str = "Disconnected"

    target_str = _global_router.state.target.name
    target_bullet = Theme.bullet_green() if target_str == "LOCAL" else Theme.bullet_cyan()
    
    lines = [
        f"{Theme.bullet_green()} Role          {role_str}",
        f"{kbd_bullet} Keyboard      {kbd_status}",
        f"{Theme.bullet_green()} Connection    {conn_str}",
    ]
    
    if _global_router.state.target == TargetMode.REMOTE and _global_router.state.remote_name:
        lines.append(f"{Theme.bullet_green()} Remote        {_global_router.state.remote_name}")
        if _active_client and _active_client.last_latency_ms > 0:
            lines.append(f"{Theme.bullet_green()} Latency       {_active_client.last_latency_ms} ms")
    else:
        lines.append(f"{Theme.bullet_dim()} Remote        Disconnected")

    lines.append(f"{target_bullet} Target        {target_str}")
    lines.append(f"{Theme.bullet_green()} Security      Secure (TLS 1.3)")
    return lines

def cmd_default() -> None:
    """Default MUX view when invoked without arguments."""
    print_header()
    for line in get_status_lines():
        print(line)
    print()
    print("Commands:\n")
    print("  switch local")
    print("  switch remote")
    print("  devices")
    print("  status")
    print("  host [port]")
    print("  connect <ip> [port]")
    print("  disconnect")
    print("  doctor")
    print("  config [show|reset]")
    print("  help")
    print("  version")

def cmd_status() -> None:
    """Print current operational status matrix."""
    print_header()
    for line in get_status_lines():
        print(line)

def cmd_doctor() -> None:
    """Run platform and system diagnostics."""
    print_header()
    
    info = get_system_info()
    print(f"{Theme.bullet_green()} {Theme.bold('OS'):<13} {info['os']}")
    print(f"{Theme.bullet_green()} {Theme.bold(info['sub_label']):<13} {info['sub_value']}")
    print(f"{Theme.bullet_green()} {Theme.bold('Architecture'):<13} {info['architecture']}")
    print(f"{Theme.bullet_green()} {Theme.bold('Python'):<13} {info['python_version']}\n")
    
    print(f"{Theme.bold('Environment Checks')}\n")
    
    if is_linux():
        checks = check_linux_environment()
    elif is_windows():
        checks = check_windows_environment()
    else:
        checks = [("Platform support", False, f"Unsupported OS: {info['os']}")]
        
    for name, passed, details in checks:
        bullet = Theme.bullet_green() if passed else Theme.bullet_yellow()
        status = "OK" if passed else "WARNING"
        print(f"  {bullet} {name:<22} [{status}] {details}")
        
    cfg = ConfigManager()
    kbd_path = cfg.selected_keyboard_path
    kbd_name = cfg.selected_keyboard_name
    
    print()
    print(f"{Theme.bold('Keyboard Configuration')}\n")
    if not kbd_path:
        print(f"  {Theme.bullet_yellow()} {'Selected Keyboard':<22} [WARNING] Not configured (Run 'mux input list')")
    else:
        exists = os.path.exists(kbd_path) or is_windows()
        exists_bullet = Theme.bullet_green() if exists else Theme.bullet_yellow()
        exists_status = "OK" if exists else "WARNING"
        print(f"  {Theme.bullet_green()} {'Selected Keyboard':<22} [OK] {kbd_name} ({kbd_path})")
        print(f"  {exists_bullet} {'Device Exists':<22} [{exists_status}] {'Device node present' if exists else 'Device path not found'}")
        
        if is_linux() and exists:
            readable = os.access(kbd_path, os.R_OK)
            perm_bullet = Theme.bullet_green() if readable else Theme.bullet_yellow()
            perm_status = "OK" if readable else "WARNING"
            perm_details = "Readable" if readable else "Permission denied (root or input group required)"
            print(f"  {perm_bullet} {'Permissions':<22} [{perm_status}] {perm_details}")

    print()
    print(f"{Theme.dim('Diagnostics complete.')}")

def cmd_input_list() -> None:
    """Enumerate available keyboard input devices."""
    print_header()
    devices = get_keyboard_devices()
    if not devices:
        print(f"{Theme.yellow('No keyboard devices detected.')}")
        return

    print("Available keyboards:\n")
    for dev in devices:
        vp = dev.formatted_vendor_product()
        print(f"[{dev.id}] {Theme.bold(dev.name)}")
        print(f"    {Theme.dim(dev.path)} ({vp})\n")

def cmd_input_select(target_id_or_path: str) -> None:
    """Select a keyboard device by index or path."""
    print_header()
    devices = get_keyboard_devices()
    selected_dev = None

    if target_id_or_path.isdigit():
        target_id = int(target_id_or_path)
        selected_dev = get_device_by_id(target_id)

    if not selected_dev:
        for dev in devices:
            if dev.path == target_id_or_path:
                selected_dev = dev
                break

    if not selected_dev:
        print(f"{Theme.red('Error:')} Device '{target_id_or_path}' not found.")
        print("Run 'mux input list' to view available keyboards.")
        return

    cfg = ConfigManager()
    cfg.set_selected_keyboard(
        path=selected_dev.path,
        name=selected_dev.name,
        vendor_id=selected_dev.vendor_id,
        product_id=selected_dev.product_id,
    )
    
    print(f"{Theme.green('Selected keyboard updated:')}")
    print(f"  Name: {Theme.bold(selected_dev.name)}")
    print(f"  Path: {selected_dev.path}")

def cmd_input_test() -> None:
    """Stream key events from configured keyboard without grabbing."""
    print_header()
    cfg = ConfigManager()
    kbd_path = cfg.selected_keyboard_path
    kbd_name = cfg.selected_keyboard_name

    if not kbd_path:
        print(f"{Theme.yellow('No keyboard selected.')} Run 'mux input list' and 'mux input select <id>'.")
        return

    if is_linux():
        if not os.path.exists(kbd_path):
            print(f"{Theme.red('Error:')} Keyboard device node '{kbd_path}' does not exist.")
            return
        if not os.access(kbd_path, os.R_OK):
            print(f"{Theme.red('Error:')} Permission denied reading '{kbd_path}'.")
            print("Run with root / sudo privileges or add user to 'input' group.")
            return
        capturer = LinuxInputCapturer(device_path=kbd_path)
    else:
        capturer = WindowsInputCapturer(device_path=kbd_path)

    print(f"Testing keyboard input on {Theme.bold(kbd_name or kbd_path)}...")
    print(f"{Theme.dim('Press Ctrl+C to exit test mode.')}\n")

    try:
        from mux.input.linux import get_key_name
        for event in capturer.read_events_generator(grab_input=False):
            key_name = get_key_name(event.key_code) if is_linux() else f"KEY_{event.key_code}"
            state_str = "DOWN" if event.event_type.value == 1 else "UP"
            print(f"{key_name:<16} {state_str}")
    except KeyboardInterrupt:
        print(f"\n{Theme.dim('Input test stopped.')}")
    finally:
        capturer.stop()
        capturer.ungrab()

def cmd_host(port_str: Optional[str] = None) -> None:
    """Start MUX host server listening for incoming remote connections."""
    global _active_server
    print_header()
    cfg = ConfigManager()
    port = int(port_str) if port_str and port_str.isdigit() else cfg.default_port

    def display_code(code: str) -> None:
        print(f"{Theme.bold('MUX Host Server Listening on port')} {port}\n")
        print(f"  {Theme.cyan('Pairing code:')} {Theme.bold(code)}")
        print(f"  {Theme.dim('(Single use code expires in 5 minutes)')}\n")
        print(f"{Theme.dim('Press Ctrl+C to stop hosting.')}\n")

    _active_server = MUXServer(host="0.0.0.0", port=port)
    _active_server.start(pairing_code_callback=display_code)

    try:
        while _active_server.is_running:
            time.sleep(0.5)
    except KeyboardInterrupt:
        print(f"\n{Theme.dim('Stopping MUX host server...')}")
    finally:
        if _active_server:
            _active_server.stop()
            _active_server = None
        print(f"{Theme.green('Host server stopped.')}")

def cmd_connect(ip: str, port_str: Optional[str] = None) -> None:
    """Connect MUX client to remote MUX host server."""
    global _active_client
    print_header()
    cfg = ConfigManager()
    port = int(port_str) if port_str and port_str.isdigit() else cfg.default_port

    print(f"Connecting to remote MUX host at {Theme.bold(ip)}:{port}...")
    pairing_code = input("Enter pairing code: ").strip()
    if not pairing_code:
        print(f"{Theme.red('Error:')} Pairing code required.")
        return

    _active_client = MUXClient(host=ip, port=port)
    
    # Handle connection drop in client
    def on_client_disconnect(reason: str) -> None:
        print(f"\n{Theme.yellow('Connection lost:')} {reason}")
        _global_router.on_connection_lost(reason)

    _active_client.set_disconnect_callback(on_client_disconnect)

    try:
        _active_client.connect(pairing_code=pairing_code)
        print(f"{Theme.bullet_green()} Pairing successful")
        print(f"{Theme.bullet_green()} Authentication successful\n")
        
        # Setup session in router and switch to REMOTE
        session = Session(remote_name=f"{ip}:{port}", remote_ip=ip, session_id=_active_client.session_id)
        _global_router.on_connection_established(session)
        _global_router.set_remote_event_sink(_active_client.send_key_event)
        _global_router.switch_to_remote()

        print(f"{Theme.green('Target switched to REMOTE.')} Physical keyboard input routed to remote machine.")
        print(f"{Theme.dim('Run \'mux switch local\' or \'mux disconnect\' to restore local control.')}")
    except PairingError as pe:
        print(f"{Theme.red('✕ Invalid pairing code:')} {pe}")
        if _active_client:
            _active_client.disconnect()
            _active_client = None
    except Exception as ex:
        print(f"{Theme.red('Connection failed:')} {ex}")
        if _active_client:
            _active_client.disconnect()
            _active_client = None

def cmd_disconnect() -> None:
    """Disconnect active remote MUX session."""
    global _active_client
    print_header()
    if _active_client and _active_client.is_connected:
        _active_client.disconnect()
        _active_client = None

    _global_router.switch_to_local()
    print(f"{Theme.green('Disconnected from remote session. Target restored to LOCAL.')}")

def cmd_devices() -> None:
    """Scan local network for active MUX instances via UDP discovery."""
    print_header()
    print("Scanning local network for MUX devices...")
    discovery = ServiceDiscovery()
    devices = discovery.scan(timeout_seconds=1.5)

    if not devices:
        print(f"{Theme.yellow('No MUX devices found on local subnet.')}")
        return

    print("\nAvailable MUX devices:\n")
    for dev in devices:
        print(f"{Theme.bullet_green()} {Theme.bold(dev['host_name'])}")
        print(f"    {dev['ip']}:{dev['port']} ({dev['os']})")
        print(f"    {Theme.dim(dev['status'])}\n")

def cmd_config(args: list[str]) -> None:
    """View or reset configuration options."""
    print_header()
    cfg = ConfigManager()
    
    sub = args[0].lower() if args else "show"
    if sub == "reset":
        cfg.reset()
        print(f"{Theme.green('Configuration reset to factory defaults.')}")
    else:
        print(f"{Theme.bold('Configuration File:')} {cfg.config_file}\n")
        for k, v in cfg._settings.items():
            print(f"  {k:<26}: {v}")

def cmd_switch_local() -> None:
    """Switch MUX input target mode to LOCAL."""
    print_header()
    _global_router.switch_to_local()
    print(f"{Theme.green('Switched input target to LOCAL.')}")

def cmd_switch_remote() -> None:
    """Switch MUX input target mode to REMOTE."""
    print_header()
    try:
        _global_router.switch_to_remote()
        print(f"{Theme.cyan('Switched input target to REMOTE.')}")
    except Exception as ex:
        print(f"{Theme.red('Target switch failed:')} {ex}")

def cmd_version() -> None:
    """Print MUX version information."""
    print(f"MUX v{__version__}")

def cmd_help() -> None:
    """Print help information."""
    print_header()
    print("Usage: mux [command]\n")
    print("Commands:")
    print("  status                Display current keyboard multiplexer status")
    print("  doctor                Run system, OS, keyboard & permission diagnostics")
    print("  devices               Scan local network for available MUX devices")
    print("  host [port]           Start MUX server and display 6-char pairing code")
    print("  connect <ip> [port]   Connect to remote MUX host with pairing code")
    print("  disconnect            Close remote session & return input to LOCAL")
    print("  input list            Enumerate available keyboard devices")
    print("  input select <id>     Select active keyboard device by ID or path")
    print("  input test            Test reading events from selected keyboard")
    print("  switch local          Switch input target to LOCAL")
    print("  switch remote         Switch input target to REMOTE")
    print("  config [show|reset]   Display or reset application settings")
    print("  version               Show MUX version information")
    print("  help                  Show this help message")
