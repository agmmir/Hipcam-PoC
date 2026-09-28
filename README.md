# Hipcam-PoC
# Hipcam-PoC

A research toolkit for detecting, brute-forcing, and capturing snapshots from
IP cameras built on the **Hipcam RealServer v1.0** platform (CVE-2023-50685).

> ⚠️ **For educational purposes and testing your own devices only.**
> Using this on systems you do not own or have written permission to test
> is illegal.

---

## Overview

The project automates three tasks:

1. **Detection** — determines whether a device is a Hipcam camera by
   inspecting RTSP and HTTP banners.
2. **Brute-force** — multi-threaded credential guessing over RTSP
   (Basic Auth, `DESCRIBE` request) against Hipcam-specific paths.
3. **Snapshot** — on successful authentication, captures a frame from the
   camera via RTSP (OpenCV) or an HTTP endpoint.

Works with a single IP or a list of IPs from a file, processing multiple
devices in parallel.

---

## Project Structure
hipcam_exploit/
├── hipcam_main.py # Entry point: loads IPs, spawns workers, writes report
├── hipcam_detect.py # Hipcam detection via RTSP/HTTP banners
├── hipcam_brute.py # Multi-threaded RTSP brute-forcer
├── hipcam_snapshot.py # Snapshot retrieval (RTSP + HTTP)
├── credentials.txt # Credentials in login:password format
├── ips.txt # List of IP addresses (one per line)
└── requirements.txt # Python dependencies

text

---

## Installation

### 1. Clone the repository

``bash
git clone https://github.com/agmmir/Hipcam-PoC.git
cd Hipcam-PoC

2. Install dependencies

bash
pip3 install -r requirements.txt
Or manually:

bash
pip3 install opencv-python-headless requests
opencv-python-headless is preferred over regular opencv-python
because it doesn't pull in GUI dependencies — snapshots are saved to
disk anyway.

If you don't need RTSP capture via OpenCV, requests alone is enough.
Usage

ips.txt format

text
192.168.1.10
192.168.1.11
10.0.0.5
# lines starting with # are ignored
credentials.txt format

Each line is login:password:

text
admin:admin
admin:12345
user:user
root:root
guest:guest
Running

bash
python3 hipcam_main.py -i ips.txt
The script will:

load IPs from ips.txt;
run detection + brute-force against each IP;
on finding valid credentials, print LOGIN: … PASSWORD: … to the log
and save a snapshot to the snapshots/ folder;
generate a results.txt report at the end.
Configuration

All key parameters are constants at the top of hipcam_main.py:

Constant	Default	Purpose
PORT	554	RTSP port
THREADS_PER_IP	10	Brute-force threads per IP
PARALLEL_IPS	5	Number of IPs processed in parallel
SNAPSHOT_DIR	"snapshots"	Folder for snapshots
TIMEOUT	5	Socket timeout, seconds
CREDENTIALS	list of pairs	Default login/password set
How Detection Works

Hipcam is identified by signatures found in server responses:

Hipcam RealServer/V1.0
Hipcam RealServer
VodServer/1.0.0
HiIpcam
Both the RTSP port (unauthenticated OPTIONS request) and the HTTP port
(GET /) are checked.

How Brute-Force Works

For each login:password pair, an RTSP request is sent:

text
DESCRIBE rtsp://<ip>:554<path> RTSP/1.0
CSeq: 2
Authorization: Basic <base64(login:password)>
Success is determined by a 200 OK response. The check runs against a
list of Hipcam-specific RTSP paths (/11, /h264_stream,
/user=admin_password=..., /tmpfs/snap.jpg, etc.).

Runs in multiple threads; on the first valid combination found, the
remaining threads stop.

How Snapshot Capture Works

RTSP — via cv2.VideoCapture, grabs the first frame and saves it
to disk.
HTTP — if RTSP fails, tries the endpoints /tmpfs/snap.jpg,
/tmpfs/auto.jpg, /snapshot.jpg, /cgi-bin/snapshot.cgi on ports
80, 8080, 8000.
Filename format: snapshots/<ip_with_underscores>.jpg.

Results

A results.txt file is created at the end:

text
IP                 Login        Password        RTSP path
----------------------------------------------------------------------
192.168.1.10       admin        tlJwpbo6        /11
192.168.1.15       user         user            /h264_stream
Snapshots are stored in the snapshots/ folder.
