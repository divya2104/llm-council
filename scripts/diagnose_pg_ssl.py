"""Stdlib-only diagnostic for the Postgres SSL handshake reset seen on Windows
(ConnectionResetError: [WinError 10054] during asyncpg's _create_ssl_connection).

No asyncpg involved, so a failure here proves the problem is TLS/network/endpoint
-level rather than anything asyncpg does. Tries the default TLS negotiation and
then a forced-TLS-1.2 negotiation, since TLS 1.3 vs 1.2 handling is a common
culprit for resets like this.

Usage (from repo root, on the Windows laptop):
    uv run python scripts/diagnose_pg_ssl.py
"""

import os
import socket
import ssl
import struct
import sys
from urllib.parse import urlparse


def load_database_url() -> str:
    if len(sys.argv) > 1:
        return sys.argv[1]
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                if line.strip().startswith("DATABASE_URL="):
                    return line.strip().split("=", 1)[1]
    raise SystemExit("DATABASE_URL not found in .env — pass it as an argument instead")


def attempt(host: str, port: int, label: str, min_version, max_version) -> None:
    print(f"\n--- {label} ---")
    try:
        sock = socket.create_connection((host, port), timeout=25)
        peer_ip, peer_port = sock.getpeername()
        print(f"TCP connect: OK — peer {peer_ip}:{peer_port}")

        # Postgres SSLRequest preamble: 4-byte length (8) + magic code 80877103
        sock.sendall(struct.pack("!ii", 8, 80877103))
        resp = sock.recv(1)
        print(f"SSLRequest response byte: {resp!r}")
        if resp != b"S":
            print("Server declined SSL upgrade — not a TLS handshake issue")
            sock.close()
            return

        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        if min_version is not None:
            ctx.minimum_version = min_version
        if max_version is not None:
            ctx.maximum_version = max_version

        with ctx.wrap_socket(sock, server_hostname=host) as tls_sock:
            print(f"TLS handshake: OK — {tls_sock.version()} {tls_sock.cipher()}")
    except Exception as e:
        print(f"FAILED: {type(e).__name__}: {e}")


def main():
    dsn = load_database_url()
    parsed = urlparse(dsn)
    host, port = parsed.hostname, parsed.port or 5432
    print(f"Target: {host}:{port}")
    print(f"OpenSSL: {ssl.OPENSSL_VERSION}")

    attempt(host, port, "default TLS negotiation", None, None)
    attempt(host, port, "forced TLS 1.2 only", ssl.TLSVersion.TLSv1_2, ssl.TLSVersion.TLSv1_2)


if __name__ == "__main__":
    main()
