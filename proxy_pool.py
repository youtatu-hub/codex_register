import requests
import json
import os
import threading
import queue
from datetime import datetime

BASE_API = "https://api.checkerproxy.net/v1/landing/archive/{}"

GITHUB_POOLS = [
    "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks5.txt",
    "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks4.txt",
    "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt"
]

TEST_URL = "https://www.google.com/"
CACHE_FILE = "proxy_cache.json"
TIMEOUT = 8
THREADS = 100


def today():
    return datetime.utcnow().strftime("%Y-%m-%d")


def fetch_checkerproxy(date):
    try:
        url = BASE_API.format(date)
        r = requests.get(url, timeout=TIMEOUT)
        r.raise_for_status()
        data = r.json()
        if not data.get("success"):
            return []
        return data["data"]["proxyList"]
    except:
        return []


def fetch_github_pool(url):
    try:
        r = requests.get(url, timeout=TIMEOUT)
        r.raise_for_status()
        lines = r.text.splitlines()
        return [x.strip() for x in lines if x.strip()]
    except:
        return []


def fetch_all_proxies():
    date = today()

    proxies = set()

    # checkerproxy
    for p in fetch_checkerproxy(date):
        proxies.add(p)
    print(len(proxies))

    # github pools
    for url in GITHUB_POOLS:
        lst = fetch_github_pool(url)
        for p in lst:
            proxies.add(p)
    print(len(proxies))
    return list(proxies)


def load_cache():
    if not os.path.exists(CACHE_FILE):
        return {}
    try:
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    except:
        return {}


def save_cache(data):
    with open(CACHE_FILE, "w") as f:
        json.dump(data, f)


def test_proxy(proxy, scheme):
    proxies = {
        "http": f"{scheme}://{proxy}",
        "https": f"{scheme}://{proxy}"
    }
    try:
        r = requests.get(TEST_URL, proxies=proxies, timeout=TIMEOUT)
        return r.status_code == 200
    except:
        return False


def test_proxy_all(proxy):
    result = {
        "proxy": proxy,
        "http": False,
        "socks4": False,
        "socks5": False
    }

    try:
        if test_proxy(proxy, "http"):
            result["http"] = True
    except:
        pass

    try:
        if test_proxy(proxy, "socks4"):
            result["socks4"] = True
    except:
        pass

    try:
        if test_proxy(proxy, "socks5"):
            result["socks5"] = True
    except:
        pass

    return result


def build_cache():
    date = today()
    cache = load_cache()

    if cache.get("date") == date and cache.get("usable"):
        return

    proxies = fetch_all_proxies()

    q = queue.Queue()
    for p in proxies:
        q.put(p)

    usable = []
    lock = threading.Lock()

    def worker():
        while True:
            try:
                proxy = q.get_nowait()
            except queue.Empty:
                return

            try:
                res = test_proxy_all(proxy)

                if res["http"] or res["socks4"] or res["socks5"]:
                    with lock:
                        usable.append(res)
            except:
                pass

            q.task_done()

    threads = []
    for _ in range(THREADS):
        t = threading.Thread(target=worker)
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    save_cache({
        "date": date,
        "usable": usable
    })


def get_proxy():
    build_cache()
    cache = load_cache()

    proxies = cache.get("usable", [])
    if not proxies:
        return None

    proxy = proxies.pop(0)

    save_cache({
        "date": cache["date"],
        "usable": proxies
    })

    return proxy


if __name__ == "__main__":
    p = get_proxy()
    print(p)