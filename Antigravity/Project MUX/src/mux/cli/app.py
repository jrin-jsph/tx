"""CLI entry point and command dispatcher for MUX."""
import sys
from typing import List, Optional
from mux.cli.commands import (
    cmd_config,
    cmd_connect,
    cmd_default,
    cmd_devices,
    cmd_disconnect,
    cmd_doctor,
    cmd_help,
    cmd_host,
    cmd_input_list,
    cmd_input_select,
    cmd_input_test,
    cmd_status,
    cmd_switch_local,
    cmd_switch_remote,
    cmd_version,
)

def run(args: Optional[List[str]] = None) -> int:
    """Main CLI entrypoint router.
    
    Returns exit code (0 for success, non-zero for errors).
    """
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    if args is None:
        args = sys.argv[1:]

    if not args:
        cmd_default()
        return 0

    command = args[0].lower()

    if command in ("help", "--help", "-h"):
        cmd_help()
        return 0
    elif command in ("version", "--version", "-v"):
        cmd_version()
        return 0
    elif command == "status":
        cmd_status()
        return 0
    elif command == "doctor":
        cmd_doctor()
        return 0
    elif command == "devices":
        cmd_devices()
        return 0
    elif command == "disconnect":
        cmd_disconnect()
        return 0
    elif command == "host":
        port_arg = args[1] if len(args) > 1 else None
        cmd_host(port_arg)
        return 0
    elif command == "connect":
        if len(args) < 2:
            print("Error: Missing IP address for 'mux connect'.\n")
            print("Usage: mux connect <ip> [port]")
            return 1
        ip_arg = args[1]
        port_arg = args[2] if len(args) > 2 else None
        cmd_connect(ip_arg, port_arg)
        return 0
    elif command == "config":
        sub_args = args[1:] if len(args) > 1 else []
        cmd_config(sub_args)
        return 0
    elif command == "input":
        if len(args) < 2:
            cmd_input_list()
            return 0
        sub_cmd = args[1].lower()
        if sub_cmd == "list":
            cmd_input_list()
            return 0
        elif sub_cmd == "test":
            cmd_input_test()
            return 0
        elif sub_cmd == "select":
            if len(args) < 3:
                print("Error: Missing device ID or path for 'mux input select'.\n")
                print("Usage: mux input select <id>")
                return 1
            cmd_input_select(args[2])
            return 0
        else:
            print(f"Unknown input subcommand: '{args[1]}'\n")
            cmd_help()
            return 1
    elif command == "switch":
        if len(args) < 2:
            print("Error: Missing target for 'mux switch'.\n")
            print("Usage: mux switch [local|remote]")
            return 1
        sub_cmd = args[1].lower()
        if sub_cmd == "local":
            cmd_switch_local()
            return 0
        elif sub_cmd == "remote":
            cmd_switch_remote()
            return 0
        else:
            print(f"Unknown switch target: '{args[1]}'\n")
            print("Usage: mux switch [local|remote]")
            return 1
    elif command in ("quit", "exit"):
        return 0
    else:
        print(f"Unknown command: '{args[0]}'\n")
        cmd_help()
        return 1
