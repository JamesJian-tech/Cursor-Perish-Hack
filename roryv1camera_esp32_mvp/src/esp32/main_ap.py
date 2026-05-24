# AP mode preview server.
# ESP32 creates hotspot and serves:
#   GET /            -> simple preview page
#   GET /snapshot.jpg -> single JPEG capture
#   GET /health      -> status JSON
# pylint: disable=import-error,no-member,broad-exception-caught
import gc
import socket
import sys
import time

import camera_freenove as cam
from ap_config import AP_CHANNEL, AP_PASSWORD, AP_SSID


def _start_ap():
    import network

    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    ap.config(
        essid=AP_SSID,
        password=AP_PASSWORD,
        authmode=network.AUTH_WPA_WPA2_PSK,
    )
    try:
        ap.config(channel=AP_CHANNEL)
    except Exception:
        pass

    # Wait briefly for AP startup.
    deadline = time.ticks_add(time.ticks_ms(), 5000)
    while not ap.active():
        if time.ticks_diff(deadline, time.ticks_ms()) <= 0:
            raise OSError("AP start timeout")
        time.sleep(0.2)

    print("AP mode ready.")
    print("SSID:", AP_SSID)
    print("IP:", ap.ifconfig()[0])
    return ap


def _resp(sock, status, content_type, body):
    header = (
        "HTTP/1.1 %s\r\n"
        "Content-Type: %s\r\n"
        "Content-Length: %d\r\n"
        "Connection: close\r\n"
        "Cache-Control: no-store\r\n"
        "\r\n"
    ) % (status, content_type, len(body))
    sock.send(header.encode())
    sock.send(body)


def _page_html(ip):
    return (
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>"
        "<title>NomSpot ESP32 Camera</title>"
        "<style>body{font-family:Arial;margin:16px;background:#111;color:#eee;}"
        "img{max-width:100%%;height:auto;"
        "border:1px solid #444;border-radius:8px;}"
        "code{background:#222;padding:2px 6px;border-radius:4px;}"
        "</style></head><body>"
        "<h2>NomSpot ESP32 Camera (AP Mode)</h2>"
        "<p>Connect WiFi: <code>%s</code> "
        "then open <code>http://%s/</code></p>"
        "<img id='frame' src='/snapshot.jpg?t=0' alt='snapshot'>"
        "<script>"
        "setInterval(function(){"
        "document.getElementById('frame').src='/snapshot.jpg?t='+Date.now();"
        "}, 2000);"
        "</script></body></html>"
    ) % (AP_SSID, ip)


def run():
    print("NomSpot AP camera preview")
    try:
        _start_ap()
        cam.init_camera()
        print("Camera init OK")
    except Exception as e:
        sys.print_exception(e)
        return

    addr = socket.getaddrinfo("0.0.0.0", 80)[0][-1]
    server = socket.socket()
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(addr)
    server.listen(1)
    print("HTTP server listening on port 80")

    try:
        while True:
            client, _ = server.accept()
            try:
                client.settimeout(5)
                req = client.recv(512)
                line = req.split(b"\r\n", 1)[0]
                parts = line.split(b" ")
                path = b"/"
                if len(parts) >= 2:
                    path = parts[1]

                ip = "192.168.4.1"
                if path == b"/" or path.startswith(b"/?"):
                    body = _page_html(ip).encode()
                    _resp(client, "200 OK", "text/html; charset=utf-8", body)
                elif path.startswith(b"/health"):
                    body = b'{"status":"ok","mode":"ap"}'
                    _resp(client, "200 OK", "application/json", body)
                elif path.startswith(b"/snapshot.jpg"):
                    jpeg = cam.capture_jpeg()
                    _resp(client, "200 OK", "image/jpeg", jpeg)
                    del jpeg
                    gc.collect()
                else:
                    _resp(client, "404 Not Found", "text/plain", b"not found")
            except Exception as e:
                sys.print_exception(e)
            finally:
                try:
                    client.close()
                except OSError:
                    pass
    finally:
        try:
            server.close()
        except OSError:
            pass
        cam.deinit_camera()
