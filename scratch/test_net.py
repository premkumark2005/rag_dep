import socket
import ssl
import httpx

target_host = "generativelanguage.googleapis.com"
target_port = 443

print(f"1. Testing DNS resolution for {target_host}...")
try:
    ip = socket.gethostbyname(target_host)
    print(f"DNS OK: {target_host} -> {ip}")
except Exception as e:
    print(f"DNS FAILED: {e}")

print(f"\n2. Testing TCP connection to {target_host}:{target_port}...")
try:
    s = socket.create_connection((target_host, target_port), timeout=10)
    print("TCP Connect OK!")
    
    print("\n3. Testing SSL handshake...")
    ctx = ssl.create_default_context()
    with ctx.wrap_socket(s, server_hostname=target_host) as ssock:
        print(f"SSL Handshake OK! Cipher: {ssock.cipher()}")
except Exception as e:
    print(f"TCP/SSL Connection FAILED: {e}")

print("\n4. Testing HTTP GET via httpx without SSL verify...")
try:
    r = httpx.get("https://generativelanguage.googleapis.com", verify=False, timeout=10)
    print(f"HTTPX GET OK: status {r.status_code}")
except Exception as e:
    print(f"HTTPX GET FAILED: {e}")
