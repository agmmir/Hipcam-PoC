# hipcam_detect.py
import socket
import re

# Сигнатуры Hipcam RealServer, встречающиеся в ответах RTSP и HTTP
HIPCAM_SIGNATURES = [
    b"Hipcam RealServer/V1.0",
    b"Hipcam RealServer",
    b"Hipcam",
    b"VodServer/1.0.0",  # Встречается в веб-интерфейсе Hipcam
    b"HiIpcam",
]

# Порты, которые обычно используют камеры Hipcam
HIPCAM_PORTS = [554, 10554, 80, 8080, 8000, 88]


def check_rtsp_banner(ip, port=554, timeout=3):
    """
    Подключается к RTSP-порту и проверяет баннер OPTIONS-запросом.
    Возвращает True, если найден признак Hipcam.
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((ip, port))

        # Отправляем OPTIONS-запрос (не требует аутентификации)
        options_req = (
            f"OPTIONS rtsp://{ip}:{port}/ RTSP/1.0\r\n"
            f"CSeq: 1\r\n"
            f"User-Agent: HipcamScanner\r\n\r\n"
        )
        sock.send(options_req.encode())

        response = sock.recv(4096)
        sock.close()

        # Ищем сигнатуры Hipcam в ответе
        for sig in HIPCAM_SIGNATURES:
            if sig in response:
                return True, response.decode(errors="ignore")
        return False, response.decode(errors="ignore")

    except (socket.error, socket.timeout):
        return False, ""


def check_http_banner(ip, port=8080, timeout=3):
    """
    Проверяет HTTP-баннер на наличие признаков Hipcam.
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((ip, port))

        http_req = (
            f"GET / HTTP/1.0\r\n"
            f"Host: {ip}:{port}\r\n"
            f"User-Agent: HipcamScanner\r\n\r\n"
        )
        sock.send(http_req.encode())

        response = sock.recv(4096)
        sock.close()

        for sig in HIPCAM_SIGNATURES:
            if sig in response:
                return True, response.decode(errors="ignore")
        return False, response.decode(errors="ignore")

    except (socket.error, socket.timeout):
        return False, ""


def detect_hipcam(ip, ports=None):
    """
    Проверяет IP-адрес на принадлежность к камерам Hipcam.
    Возвращает кортеж (is_hipcam, port, banner_info).
    """
    if ports is None:
        ports = HIPCAM_PORTS

    for port in ports:
        if port in (554, 10554):
            is_hip, banner = check_rtsp_banner(ip, port)
            if is_hip:
                return True, port, banner
        elif port in (80, 8080, 8000, 88):
            is_hip, banner = check_http_banner(ip, port)
            if is_hip:
                return True, port, banner

    return False, None, ""
