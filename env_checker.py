import requests
import json
import base64
import urllib3
from datetime import datetime
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
from config import RSA_PUBLIC_KEY, LOGIN_API, TOKENSELL_API_URL, API_KEY

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class EnvChecker:
    def __init__(self):
        self.log_file = "log.txt"
        self.proxy_file = "proxy.txt"
        self.proxy_dict = self._load_proxy()

    def log(self, tag: str, status: bool, message: str):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        indicator = "✅" if status else "❌"
        line = f"[{ts}] {indicator} [{tag}] - {message}"
        print(line)
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(line + "\n")

    def _load_proxy(self):
        try:
            with open(self.proxy_file, "r", encoding="utf-8") as f:
                lines = [l.strip() for l in f if l.strip()]
                if not lines: return None
                
                proxy_str = lines[0]
                parts = proxy_str.split(":")
                if len(parts) == 4:
                    h, p, u, pw = parts
                    url = f"http://{u}:{pw}@{h}:{p}"
                elif len(parts) == 2:
                    h, p = parts
                    url = f"http://{h}:{p}"
                else:
                    return None
                return {"http": url, "https": url}
        except Exception as e:
            print(f"[PROXY] Lỗi đọc file proxy: {e}")
        return None

    def check_proxy(self):
        if not self.proxy_dict:
            self.log("PROXY", False, "Không có proxy hoặc sai định dạng (h:p:u:pw)")
            return False
        try:
            r = requests.get("https://httpbin.org/ip", proxies=self.proxy_dict, timeout=15)
            if r.status_code == 200:
                ip = r.json().get("origin")
                self.log("PROXY", True, f"Kết nối OK | IP: {ip}")
                return True
        except Exception as e:
            self.log("PROXY", False, f"Lỗi kết nối: {str(e)}")
        return False

    def check_login_api(self):
        try:
            r = requests.get(LOGIN_API, timeout=20, verify=False)
            self.log("LOGIN_API", r.status_code < 500, f"HTTP {r.status_code}")
            return r.status_code < 500
        except Exception as e:
            self.log("LOGIN_API", False, str(e))
            return False

    def check_tokensell_api(self):
        try:
            payload = {"apikey": API_KEY, "type": "datadome"}
            r = requests.post(f"{TOKENSELL_API_URL}/api/task/createtask", json=payload, timeout=20)
            data = r.json()
            if data.get("status"):
                self.log("TOKENSELL", True, f"Task created | ID: {data.get('taskId')}")
                return True
            self.log("TOKENSELL", False, data.get("message", "Unknown error"))
        except Exception as e:
            self.log("TOKENSELL", False, str(e))
        return False

    def check_rsa_key(self):
        try:
            key = RSA.import_key(RSA_PUBLIC_KEY)
            cipher = PKCS1_v1_5.new(key)
            if cipher.encrypt(b"test"):
                self.log("RSA", True, "Key hợp lệ")
                return True
        except Exception as e:
            self.log("RSA", False, str(e))
        return False

    def run_all_checks(self):
        self.log("SYSTEM", True, "Bắt đầu kiểm tra môi trường...")
        results = [
            self.check_proxy(),
            self.check_login_api(),
            self.check_tokensell_api(),
            self.check_rsa_key()
        ]
        self.log("SYSTEM", True, "Hoàn tất kiểm tra.")
        return all(results)