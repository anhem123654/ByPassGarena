import requests # type: ignore
import json
import base64
from datetime import datetime
from Crypto.PublicKey import RSA # type: ignore
from Crypto.Cipher import PKCS1_v1_5 # type: ignore

from config import (
    RSA_PUBLIC_KEY,
    LOGIN_API,
    DATADOME_FILE,
    TOKENSELL_API_URL,
    API_KEY
)

LOG_FILE = "log.txt"
PROXY_FILE = "proxy.txt"


class EnvChecker:
    def __init__(self):
        self.proxy_string = self._load_proxy()

    def log(self, tag: str, status: bool, message: str):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{ts}] [{tag}] {'SUCCESS' if status else 'FAILED'} - {message}"
        print(line)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")

    def _load_proxy(self):
        try:
            with open(PROXY_FILE, "r", encoding="utf-8") as f:
                return f.read().strip()
        except:
            return ""

    def _parse_proxy(self):
        try:
            h, p, u, pw = self.proxy_string.split(":", 3)
            return {
                "http": f"http://{u}:{pw}@{h}:{p}",
                "https": f"http://{u}:{pw}@{h}:{p}",
            }
        except:
            return None

    def check_proxy(self):
        if not self.proxy_string:
            self.log("PROXY", False, "proxy.txt trống hoặc không tồn tại")
            return False

        proxy = self._parse_proxy()
        if not proxy:
            self.log("PROXY", False, "Sai format proxy")
            return False

        try:
            r = requests.get(
                "https://httpbin.org/ip",
                proxies=proxy,
                timeout=15
            )
            if r.status_code == 200:
                ip = r.json().get("origin", "unknown")
                self.log("PROXY", True, f"Kết nối OK | IP: {ip}")
                return True
            else:
                self.log("PROXY", False, f"HTTP {r.status_code}")
        except Exception as e:
            self.log("PROXY", False, str(e))

        return False

    def check_login_api(self):
        try:
            r = requests.get(
                LOGIN_API,
                timeout=20,
                verify=False
            )
            ct = r.headers.get("Content-Type", "")
            if r.status_code < 500:
                self.log("LOGIN_API", True, f"HTTP {r.status_code} | Content-Type: {ct}")
                return True
            else:
                self.log("LOGIN_API", False, f"HTTP {r.status_code}")
        except Exception as e:
            self.log("LOGIN_API", False, str(e))
        return False

    def check_tokensell_api(self):
        try:
            url = f"{TOKENSELL_API_URL}/api/task/createtask"
            payload = {
                "apikey": API_KEY,
                "type": "datadome"
            }

            r = requests.post(url, json=payload, timeout=20)
            if r.status_code != 200:
                self.log("TOKENSELL", False, f"HTTP {r.status_code}")
                return False

            data = r.json()
            if data.get("status") and "taskId" in data:
                self.log("TOKENSELL", True, f"Task created | ID: {data['taskId']}")
                return True
            else:
                self.log("TOKENSELL", False, data.get("message", "Unknown error"))
        except Exception as e:
            self.log("TOKENSELL", False, str(e))

        return False

    def check_rsa_key(self):
        try:
            key = RSA.import_key(RSA_PUBLIC_KEY)
            cipher = PKCS1_v1_5.new(key)
            encrypted = cipher.encrypt(b"test-password")
            if encrypted:
                b64 = base64.b64encode(encrypted).decode()
                self.log("RSA", True, f"Encrypt OK | len={len(b64)}")
                return True
        except Exception as e:
            self.log("RSA", False, str(e))

        return False

    def run_all_checks(self):
        self.log("SYSTEM", True, "Bắt đầu kiểm tra môi trường")

        self.check_proxy()
        self.check_login_api()
        self.check_tokensell_api()
        self.check_rsa_key()

        self.log("SYSTEM", True, "Hoàn tất kiểm tra")