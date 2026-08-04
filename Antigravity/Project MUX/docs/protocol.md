# MUX Wire Protocol Specification

## Overview

MUX operates a length-prefixed protocol over TCP streams (`PROTOCOL_VERSION = 1`).

## Frame Structure

```
+-------------------+------------------------------------------+
| Length (4 Bytes)  | JSON Payload (N Bytes, max 64 KB)        |
+-------------------+------------------------------------------+
```

- **Length Header**: 4-byte big-endian unsigned integer (`struct.pack('>I', payload_length)`).
- **JSON Payload**: UTF-8 encoded string containing standard message structure.

## Message Schema

```json
{
  "version": 1,
  "type": "KEY_EVENT",
  "session_id": "sess-client-123",
  "seq": 42,
  "payload": {
    "key_code": 30,
    "event_type": 1,
    "timestamp": 1740000000.123,
    "sequence_number": 42,
    "modifiers": {
      "shift": true,
      "ctrl": false,
      "alt": false,
      "meta": false,
      "caps_lock": false,
      "num_lock": false
    }
  }
}
```

## Message Types

- `HELLO`: Protocol handshake initialization.
- `PAIR_REQUEST`: Client pairing submission with 6-character code.
- `PAIR_RESPONSE`: Host pairing result.
- `KEY_EVENT`: Encrypted keyboard scancode event stream.
- `PING` / `PONG`: Heartbeat keepalive (2s interval, 5s timeout).
- `SWITCH_TARGET`: Input routing target synchronization.
- `DISCONNECT`: Graceful session termination.
- `ERROR`: Diagnostic failure response.
