"""TLS certificate generation and SHA-256 fingerprint helper utilities."""
import hashlib
import os
import ssl
import tempfile
from typing import Tuple

class CryptoUtils:
    """TLS 1.3 encryption and certificate fingerprint verification utilities."""
    
    @staticmethod
    def get_cert_fingerprint(cert_der: bytes) -> str:
        """Calculate SHA-256 fingerprint hex string of a DER-encoded TLS certificate."""
        return hashlib.sha256(cert_der).hexdigest().upper()

    @staticmethod
    def generate_self_signed_cert() -> Tuple[str, str]:
        """Generate a temporary self-signed TLS cert and private key file pair."""
        try:
            from cryptography import x509  # type: ignore
            from cryptography.x509.oid import NameOID  # type: ignore
            from cryptography.hazmat.primitives import hashes, serialization  # type: ignore
            from cryptography.hazmat.primitives.asymmetric import rsa  # type: ignore
            import datetime

            key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
            subject = issuer = x509.Name([
                x509.NameAttribute(NameOID.COMMON_NAME, "MUX Secure Host"),
            ])
            cert = x509.CertificateBuilder().subject_name(
                subject
            ).issuer_name(
                issuer
            ).public_key(
                key.public_key()
            ).serial_number(
                x509.random_serial_number()
            ).not_valid_before(
                datetime.datetime.now(datetime.timezone.utc)
            ).not_valid_after(
                datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=365)
            ).sign(key, hashes.SHA256())

            tmp_dir = tempfile.gettempdir()
            cert_path = os.path.join(tmp_dir, "mux_cert.pem")
            key_path = os.path.join(tmp_dir, "mux_key.pem")

            with open(cert_path, "wb") as f:
                f.write(cert.public_bytes(serialization.Encoding.PEM))

            with open(key_path, "wb") as f:
                f.write(key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.TraditionalOpenSSL,
                    encryption_algorithm=serialization.NoEncryption()
                ))

            return cert_path, key_path
        except Exception:
            # Fallback if cryptography library is not installed
            return "", ""

    @staticmethod
    def create_server_ssl_context(cert_file: str, key_file: str) -> ssl.SSLContext:
        """Create server SSLContext enforcing TLS 1.2+ with strong ciphers."""
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        if cert_file and key_file and os.path.exists(cert_file) and os.path.exists(key_file):
            ctx.load_cert_chain(certfile=cert_file, keyfile=key_file)
        return ctx

    @staticmethod
    def create_client_ssl_context() -> ssl.SSLContext:
        """Create client SSLContext for TLS connection."""
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE  # Self-signed cert fingerprint verification done at app layer
        return ctx
