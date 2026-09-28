# hipcam_snapshot.py
import cv2
import requests
import os


def snapshot_via_rtsp(ip, port, username, password, path, output_file="snapshot.jpg"):
    """
    Получает снимок через RTSP-поток с помощью OpenCV.
    Возвращает True, если снимок сохранен.
    """
    rtsp_url = f"rtsp://{username}:{password}@{ip}:{port}{path}"

    try:
        cap = cv2.VideoCapture(rtsp_url)
        if not cap.isOpened():
            print(f"[-] Не удалось открыть RTSP-поток: {rtsp_url}")
            return False

        ret, frame = cap.read()
        cap.release()

        if ret:
            cv2.imwrite(output_file, frame)
            print(f"[+] Снимок сохранен: {output_file}")
            return True
        else:
            print("[-] Не удалось захватить кадр")
            return False

    except Exception as e:
        print(f"[-] Ошибка RTSP: {e}")
        return False


def snapshot_via_http(ip, port, username, password, output_file="snapshot.jpg"):
    """
    Получает снимок через HTTP-эндпоинт.
    Пробует несколько характерных для Hipcam путей.
    """
    # Пути для HTTP-снимков, встречающиеся у Hipcam
    http_snapshot_paths = [
        "/tmpfs/snap.jpg",
        "/tmpfs/auto.jpg",
        "/snapshot.jpg",
        "/cgi-bin/snapshot.cgi",
    ]

    for path in http_snapshot_paths:
        url = f"http://{ip}:{port}{path}"
        try:
            response = requests.get(
                url,
                auth=(username, password),
                timeout=5,
                stream=True
            )
            if response.status_code == 200:
                with open(output_file, "wb") as f:
                    f.write(response.content)
                print(f"[+] HTTP-снимок сохранен: {output_file} ({url})")
                return True
        except requests.RequestException:
            continue

    print("[-] Не удалось получить HTTP-снимок")
    return False


def get_snapshot(ip, port, username, password, rtsp_path=None, output_file="snapshot.jpg"):
    """
    Универсальная функция получения снимка:
    сначала пробует RTSP, затем HTTP.
    """
    # Если известен рабочий RTSP-путь — используем его
    if rtsp_path:
        return snapshot_via_rtsp(ip, port, username, password, rtsp_path, output_file)

    # Иначе пробуем стандартные пути
    default_rtsp_paths = ["/11", "/1", "/h264_stream", "/Streaming/Channels/1"]
    for path in default_rtsp_paths:
        if snapshot_via_rtsp(ip, port, username, password, path, output_file):
            return True

    # Если RTSP не сработал — пробуем HTTP
    return snapshot_via_http(ip, port, username, password, output_file)
