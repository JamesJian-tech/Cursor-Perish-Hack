# POST JPEG frames to the laptop backend (Phase 2).
# Uses raw sockets — lemariva camera firmware has no urequests module.
import gc
import socket


def _parse_http_url(url):
    if not url.startswith("http://"):
        raise ValueError("only http:// URLs supported")
    rest = url[7:]
    slash = rest.find("/")
    if slash == -1:
        host_port, path = rest, "/"
    else:
        host_port, path = rest[:slash], rest[slash:]
    if ":" in host_port:
        host, port_s = host_port.rsplit(":", 1)
        port = int(port_s)
    else:
        host, port = host_port, 80
    return host, port, path


def post_jpeg(url, jpeg_bytes, timeout=15, retries=2):
    """POST raw JPEG body to BACKEND_URL. Returns HTTP status or None on failure."""
    if not jpeg_bytes:
        return None

    for attempt in range(retries):
        status = _post_jpeg_once(url, jpeg_bytes, timeout)
        if status is not None and 200 <= status < 300:
            return status
        if attempt + 1 < retries:
            print("upload retry", attempt + 2)
    return status


def _post_jpeg_once(url, jpeg_bytes, timeout):
    sock = None
    try:
        host, port, path = _parse_http_url(url)
        addr = socket.getaddrinfo(host, port)[0][-1]
        sock = socket.socket()
        sock.settimeout(timeout)
        sock.connect(addr)

        headers = (
            "POST {path} HTTP/1.1\r\n"
            "Host: {host}:{port}\r\n"
            "Content-Type: image/jpeg\r\n"
            "Content-Length: {length}\r\n"
            "Connection: close\r\n"
            "\r\n"
        ).format(
            path=path,
            host=host,
            port=port,
            length=len(jpeg_bytes),
        )
        sock.send(headers.encode())
        sock.send(jpeg_bytes)

        status_line = b""
        while b"\r\n" not in status_line and len(status_line) < 128:
            chunk = sock.recv(64)
            if not chunk:
                break
            status_line += chunk

        parts = status_line.split(b" ", 2)
        if len(parts) >= 2:
            return int(parts[1])
        return None
    except OSError as e:
        print("upload error:", e)
        return None
    except ValueError as e:
        print("upload error:", e)
        return None
    finally:
        if sock is not None:
            try:
                sock.close()
            except OSError:
                pass
        gc.collect()
