from concurrent.futures import ThreadPoolExecutor

from env_checker import EnvChecker
from account_loader import AccountLoader

MAX_THREADS = 5


def main():
    # ---------- step 1: env check ----------
    checker = EnvChecker()
    checker.run_all_checks()

    # ---------- step 2: load account ----------
    account_loader = AccountLoader()
    accounts = account_loader.accounts

    if not accounts:
        print("[SYSTEM] Không có account, dừng tool")
        return

    # ---------- step 3: chọn số luồng ----------
    try:
        threads = int(input(f"Nhập số luồng (1-{MAX_THREADS}): ").strip())
    except ValueError:
        threads = 1

    threads = max(1, min(threads, MAX_THREADS))
    print(f"[SYSTEM] Chạy với {threads} luồng")

    # ---------- step 4: login ----------
    with ThreadPoolExecutor(max_workers=threads) as executor:
        executor.map(account_loader.login_account, accounts)

    print("[SYSTEM] Login batch hoàn tất")


if __name__ == "__main__":
    main()
