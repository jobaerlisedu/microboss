# Start CMS with HTTPS
Write-Host "Starting CHANNEL ONE DIGITAL CMS with HTTPS..." -ForegroundColor Yellow
$venv = Join-Path $PSScriptRoot "venv\Scripts\python.exe"
$certs = Join-Path $PSScriptRoot "certs"
if (-not (Test-Path (Join-Path $certs "server.crt"))) {
    Write-Host "Generating self-signed certificate..." -ForegroundColor Cyan
    & $venv -c @"
import datetime, os, ssl, ipaddress
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
key = rsa.generate_private_key(65537, 2048, default_backend())
subject = issuer = x509.Name([
    x509.NameAttribute(NameOID.COUNTRY_NAME, 'BD'),
    x509.NameAttribute(NameOID.ORGANIZATION_NAME, 'Channel One Digital'),
    x509.NameAttribute(NameOID.COMMON_NAME, '127.0.0.1'),
])
cert = (x509.CertificateBuilder()
    .subject_name(subject).issuer_name(issuer)
    .public_key(key.public_key()).serial_number(x509.random_serial_number())
    .not_valid_before(datetime.datetime.utcnow())
    .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=365*5))
    .add_extension(x509.SubjectAlternativeName([
        x509.DNSName('localhost'), x509.IPAddress(ipaddress.IPv4Address('127.0.0.1'))
    ]), critical=False)
    .sign(key, hashes.SHA256(), default_backend()))
os.makedirs('certs', exist_ok=True)
with open('certs/server.key', 'wb') as f:
    f.write(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.TraditionalOpenSSL, serialization.NoEncryption()))
with open('certs/server.crt', 'wb') as f:
    f.write(cert.public_bytes(serialization.Encoding.PEM))
print('Certificate generated')
"@
}
Write-Host "HTTPS: https://127.0.0.1:8443/" -ForegroundColor Green
Write-Host "HTTP:  http://127.0.0.1:8000/" -ForegroundColor Green
Start-Process -FilePath $venv -ArgumentList "manage.py runsslserver --certificate certs\server.crt --key certs\server.key 0.0.0.0:8443 --noreload" -WorkingDirectory $PSScriptRoot -WindowStyle Hidden
Start-Process -FilePath $venv -ArgumentList "manage.py runserver 0.0.0.0:8000 --noreload" -WorkingDirectory $PSScriptRoot -WindowStyle Hidden
Write-Host "Server started. Press any key to stop..." -ForegroundColor Cyan
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
Get-Process -Name python -ErrorAction SilentlyContinue | Stop-Process -Force
Write-Host "Servers stopped." -ForegroundColor Yellow
