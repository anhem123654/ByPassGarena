import requests  # type: ignore
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import urllib3 # type: ignore
import json

from config import LOGIN_API

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

ACCOUNT_FILE = "account.txt"
LOG_FILE = "AccountLog.txt"

log_lock = threading.Lock()


class AccountLoader:
    def __init__(self, max_threads: int = 1):
        self.max_threads = max_threads
        self.accounts = self._load_accounts()

    def _log(self, username: str, status: bool, message: str):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{ts}] [{username}] {'SUCCESS' if status else 'FAILED'} - {message}"
        print(line)
        with log_lock:
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(line + "\n")

    def _load_accounts(self):
        accounts = []
        try:
            with open(ACCOUNT_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or "|" not in line:
                        continue
                    accounts.append(line)
        except Exception as e:
            print(f"[ACCOUNT] Không đọc được account.txt: {e}")

        print(f"[ACCOUNT] Loaded {len(accounts)} account")
        return accounts

    def login_account(self, account_line: str) -> bool:
        username = "UNKNOWN"
        try:
            username, password = account_line.split("|", 1)
            url = f"{LOGIN_API}?username={username}&password={password}"

            r = requests.get(url, timeout=20, verify=False)

            try:
                data = r.json()
                code = data.get("code")

                if code == 0:
                    self._log(username, True, "Login OK")
                    return True

                if code in (-1, 3, 101):
                    self._log(username, False, f"Login failed | code={code}")
                    return False

                self._log(username, False, f"Unknown JSON | code={code}")
                return False

            except json.JSONDecodeError:
                ct = r.headers.get("Content-Type", "")
                preview = r.text[:80].replace("\n", " ")
                self._log(
                    username,
                    False,
                    f"Non-JSON response | CT={ct} | PREVIEW={preview}"
                )
                return False

        except Exception as e:
            self._log(username, False, f"Exception: {e}")
            return False

    def run(self):
        if not self.accounts:
            print("[ACCOUNT] Không có account để chạy")
            return

        with open(LOG_FILE, "w", encoding="utf-8") as f:
            f.write(f"# Account login log - {datetime.now()}\n")

        print(f"[SYSTEM] Chạy với {self.max_threads} luồng")

        with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
            futures = [
                executor.submit(self.login_account, acc)
                for acc in self.accounts
            ]

            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"[THREAD] Lỗi: {e}")
