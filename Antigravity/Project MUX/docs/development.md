# MUX Development Guide

## Environment Setup

1. **Clone repository & install dependencies**:
   ```bash
   pip install -e .[dev]
   ```

2. **Run full pytest suite**:
   ```bash
   python -m pytest -v
   ```

3. **Run CLI commands locally**:
   ```bash
   python -m mux status
   python -m mux doctor
   python -m mux devices
   python -m mux config show
   ```

4. **Host & Connect Loopback Verification**:
   ```bash
   # Terminal 1 (Host)
   python -m mux host

   # Terminal 2 (Client)
   python -m mux connect 127.0.0.1
   ```
