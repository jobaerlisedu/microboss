"""Generate self-signed certificate for development HTTPS server."""
import datetime
import ipaddress
import ssl
import os

CERT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'certs')
os.makedirs(CERT_DIR, exist_ok=True)

CERT_FILE = os.path.join(CERT_DIR, 'server.crt')
KEY_FILE = os.path.join(CERT_DIR, 'server.key')

# Generate using Python's ssl module with a self-signed cert via temp context
try:
    from cryptography import x509
    from cryptography.x509.oid import NameOID
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.backends import default_backend

    key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend(),
    )

    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, 'BD'),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, 'Dhaka'),
        x509.NameAttribute(NameOID.LOCALITY_NAME, 'Dhaka'),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, 'Channel One Digital'),
        x509.NameAttribute(NameOID.COMMON_NAME, '127.0.0.1'),
    ])

    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.utcnow())
        .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=365))
        .add_extension(x509.SubjectAlternativeName([
            x509.DNSName('localhost'),
            x509.IPAddress(ipaddress.IPv4Address('127.0.0.1')),
        ]), critical=False)
        .sign(key, hashes.SHA256(), backend=default_backend())
    )

    with open(KEY_FILE, 'wb') as f:
        f.write(key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        ))

    with open(CERT_FILE, 'wb') as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))

    print(f'Certificate generated: {CERT_FILE}')
    print(f'Private key generated: {KEY_FILE}')

except ImportError:
    print('cryptography not available. Trying PowerShell method...')
    # Fallback: use PowerShell New-SelfSignedCertificate
    import subprocess
    import tempfile

    ps_script = f'''
    $cert = New-SelfSignedCertificate -DnsName "localhost","127.0.0.1" -CertStoreLocation "cert:\\LocalMachine\\My" -FriendlyName "Django Dev Cert" -NotAfter (Get-Date).AddYears(1)
    $pwd = ConvertTo-SecureString -String "password" -Force -AsPlainText
    Export-PfxCertificate -Cert $cert -FilePath "{CERT_DIR}\\server.pfx" -Password $pwd
    $cert | Export-Certificate -FilePath "{CERT_FILE}" -Type CERT
    openssl pkcs12 -in "{CERT_DIR}\\server.pfx" -nocerts -out "{KEY_FILE}" -nodes -password pass:password
    '''

    result = subprocess.run(['powershell', '-Command', ps_script], capture_output=True, text=True)
    if result.returncode == 0:
        print(f'Certificate generated via PowerShell')
    else:
        print(f'PowerShell cert generation failed: {result.stderr}')
        print('Install cryptography: pip install cryptography')
