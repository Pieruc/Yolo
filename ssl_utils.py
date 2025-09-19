import os
import ipaddress
from datetime import datetime, timedelta
import logging

def generate_self_signed_cert(cert_file='server.crt', key_file='server.key', ip_list=None):
    """Genera certificato auto-firmato se non esiste"""
    if os.path.exists(cert_file) and os.path.exists(key_file):
        logging.info(f"[SSL] Certificati esistenti trovati: {cert_file}, {key_file}")
        return cert_file, key_file

    try:
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        import socket

        logging.info("[SSL] Generazione certificato auto-firmato...")

        # Chiave privata
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

        # Subject e issuer
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "IT"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Marche"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "Jesi"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "YOLO Server"),
            x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
        ])

        # Indirizzi IP dinamici
        if ip_list is None:
            ip_list = ["127.0.0.1"]
            try:
                hostname_ip = socket.gethostbyname(socket.gethostname())
                ip_list.append(hostname_ip)
            except Exception:
                pass

        alt_names = [x509.DNSName("localhost")]
        for ip in ip_list:
            try:
                alt_names.append(x509.IPAddress(ipaddress.IPv4Address(ip)))
            except Exception:
                continue

        cert = x509.CertificateBuilder().subject_name(subject).issuer_name(issuer)\
            .public_key(private_key.public_key())\
            .serial_number(x509.random_serial_number())\
            .not_valid_before(datetime.utcnow())\
            .not_valid_after(datetime.utcnow() + timedelta(days=365))\
            .add_extension(x509.SubjectAlternativeName(alt_names), critical=False)\
            .sign(private_key, hashes.SHA256())

        # Scrivi file
        with open(cert_file, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
        with open(key_file, "wb") as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))

        logging.info(f"[SSL] ✓ Certificato generato: {cert_file}")
        logging.info(f"[SSL] ✓ Chiave privata generata: {key_file}")
        logging.warning("[SSL] Certificato auto-firmato: i browser mostreranno avviso di sicurezza")

        return cert_file, key_file

    except ImportError:
        logging.error("[SSL] Modulo 'cryptography' non trovato. Installa con: pip install cryptography")
        return None, None
    except Exception as e:
        logging.error(f"[SSL] Errore generazione certificato: {e}")
        return None, None
