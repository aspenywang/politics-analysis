import aiohttp
import asyncio
import re
import os
import time
from aiohttp import ClientSession, ClientTimeout

class Proxy:
    def __init__(self):
        self.connect_timeout = 2  # Connection timeout in seconds
        self.read_timeout = 1     # Read timeout in seconds
        self.timeout = ClientTimeout(
            connect=self.connect_timeout,
            total=self.connect_timeout + self.read_timeout
        )
        self.speed_threshold = 2  # Only keep proxies faster than this (seconds)
        self.test_url = "http://httpbin.org/get"  # Lightweight test URL
        self.concurrency_limit = 200  # Adjust based on your system's capabilities

    async def test_proxy_speed(self, session: ClientSession, proxy: str):
        """Asynchronously test a single proxy's speed"""
        try:
            start_time = time.time()
            async with session.get(
                    self.test_url,
                    proxy=f"http://{proxy}",
                    timeout=self.timeout
            ) as response:
                if response.status == 200:
                    response_time = time.time() - start_time
                    return (proxy, response_time)
                return None
        except Exception:
            return None

    async def get_proxy_list(self):
        """Fetch and test proxies asynchronously"""
        file_path = "Proxy/proxies_list.txt"
        good_proxies = []

        # Corrected raw proxy list URL
        proxy_source_url = "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt"

        try:
            print("Fetching proxies from GitHub...")
            async with ClientSession() as session:
                # Fetch proxy list
                async with session.get(proxy_source_url) as response:
                    raw_text = await response.text()
                    raw_proxies = re.findall(r"\d+\.\d+\.\d+\.\d+:\d+", raw_text)

                    if not raw_proxies:
                        print("Warning: No proxies found!")
                        return

                    print(f"Testing {len(raw_proxies)} proxies for speed...")

                    # Configure connection pool
                    connector = aiohttp.TCPConnector(limit=self.concurrency_limit)
                    async with ClientSession(
                            connector=connector,
                            timeout=self.timeout
                    ) as test_session:
                        tasks = [self.test_proxy_speed(test_session, p) for p in raw_proxies]
                        results = await asyncio.gather(*tasks)

                        for result in results:
                            if result:
                                proxy, speed = result
                                if speed < self.speed_threshold:
                                    good_proxies.append(proxy)
                                    print(f"✓ {proxy} ({speed:.2f}s)")
                                else:
                                    print(f"✗ {proxy} too slow ({speed:.2f}s)")

            # Save valid proxies
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w') as f:
                f.write("\n".join(good_proxies))

            print(f"\nSaved {len(good_proxies)} fast proxies to {file_path}")

        except Exception as e:
            print(f"Error: {e}")
