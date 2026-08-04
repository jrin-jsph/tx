# MUX Security Model

## Threat Model & Principles

1. **Established Cryptography**: MUX strictly utilizes standard libraries (`secrets`, `ssl`, `cryptography`, `hashlib`) for security.
2. **Mutual Authentication & Pairing**:
   - Out-of-band 6-character alphanumeric pairing code generated via `secrets.choice()`.
   - Single-use verification with 300-second expiration.
   - Rate-limiting locking out IPs after 5 failed attempts.
   - Pairing code is never logged, stored in plaintext, or used directly as the encryption key.
3. **Transport Encryption**:
   - TLS 1.3 / TLS 1.2 encrypted socket connections (`ssl.SSLContext`).
   - SHA-256 certificate fingerprint pinning.
   - Monotonic sequence numbers providing replay protection.
4. **Local Network Boundary**: Discovery broadcasts are limited to local subnets.
