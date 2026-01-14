import asyncio
import json
import logging
import time
import random
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple

import aiohttp
from tqdm.asyncio import tqdm_asyncio


@dataclass(frozen=True)
class ProxyQuality:
    """Single proxy quality check result"""

    proxy: str
    latency_ms: int
    services_ok: int
    services: Dict[str, Dict[str, Any]]


class ProxyDog:
    # Public proxy sources (quality may vary A LOT)
    _SOURCES: Tuple[str, ...] = (
         'https://api.proxyscrape.com/v4/free-proxy-list/get?request=get_proxies&protocol=http&proxy_format=ipport&format=text&anonymity=Elite&timeout=20000',
         'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt',
        # 'https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt',
        # 'https://raw.githubusercontent.com/r00tee/Proxy-List/refs/heads/main/Https.txt',
        # 'https://raw.githubusercontent.com/Vann-Dev/proxy-list/refs/heads/main/proxies/http.txt',
        # 'https://raw.githubusercontent.com/Vann-Dev/proxy-list/refs/heads/main/proxies/https.txt',
        # 'https://raw.githubusercontent.com/elliottophellia/proxylist/master/results/pmix_checked.txt',
        # 'https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/protocols/http/data.txt',
        # 'https://raw.githubusercontent.com/ALIILAPRO/Proxy/main/http.txt',
        # 'https://raw.githubusercontent.com/andigwandi/free-proxy/main/proxy_list.txt',
        # 'https://raw.githubusercontent.com/ErcinDedeoglu/proxies/main/proxies/http.txt',
        # 'https://raw.githubusercontent.com/mmpx12/proxy-list/master/proxies.txt',
        # 'https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/all.txt',
        # 'https://raw.githubusercontent.com/monosans/proxy-list/main/proxies_anonymous/all.txt',
        # 'https://raw.githubusercontent.com/roosterkid/openproxylist/main/HTTPS_RAW.txt',
        # 'https://raw.githubusercontent.com/SevenworksDev/proxy-list/main/proxies/unknown.txt',
        # 'https://raw.githubusercontent.com/sunny9577/proxy-scraper/master/proxies.txt',
        # 'https://raw.githubusercontent.com/themiralay/Proxy-List-World/master/data.txt',
        # 'https://raw.githubusercontent.com/Tsprnay/Proxy-lists/master/proxies/http.txt',
        # 'https://raw.githubusercontent.com/TuanMinPay/live-proxy/master/http.txt',
        # 'https://raw.githubusercontent.com/Zaeem20/FREE_PROXIES_LIST/master/http.txt',
        # 'https://raw.githubusercontent.com/zevtyardt/proxy-list/main/http.txt',
        # 'https://github.com/zloi-user/hideip.me/raw/refs/heads/master/http.txt',
        # 'https://github.com/zloi-user/hideip.me/raw/refs/heads/master/connect.txt',
        # 'https://raw.githubusercontent.com/dinoz0rg/proxy-list/main/scraped_proxies/http.txt',
        # 'https://raw.githubusercontent.com/zebbern/Proxy-Scraper/main/http.txt',
        # 'https://raw.githubusercontent.com/yemixzy/proxy-list/main/proxies/unchecked.txt',
        # 'https://raw.githubusercontent.com/yemixzy/proxy-list/main/proxies/http.txt',
        # 'https://raw.githubusercontent.com/vmheaven/VMHeaven-Free-Proxy-Updated/main/http.txt',
        # 'https://raw.githubusercontent.com/saisuiu/Lionkings-Http-Proxys-Proxies/refs/heads/main/free.txt',
        # 'https://raw.githubusercontent.com/FifzzSENZE/Master-Proxy/master/proxies/http.txt',
        # 'https://raw.githubusercontent.com/fyvri/fresh-proxy-list/archive/storage/classic/http.txt',
        # 'https://github.com/handeveloper1/Proxy/raw/refs/heads/main/Proxies-Ercin/http.txt',
        # 'https://github.com/Anonym0usWork1221/Free-Proxies/raw/refs/heads/main/proxy_files/http_proxies.txt',
        # 'https://github.com/zenjahid/FreeProxy4u/raw/refs/heads/main/http.txt',
        # 'https://raw.githubusercontent.com/BreakingTechFr/Proxy_Free/refs/heads/main/proxies/http.txt',
        # 'https://raw.githubusercontent.com/VolkanSah/Auto-Proxy-Fetcher/refs/heads/main/proxies.txt',
        # 'https://raw.githubusercontent.com/databay-labs/free-proxy-list/refs/heads/master/http.txt',
        # 'https://raw.githubusercontent.com/ProxyScraper/ProxyScraper/refs/heads/main/http.txt',
        # 'https://raw.githubusercontent.com/variableninja/proxyscraper/refs/heads/main/proxies/http.txt',
        # 'https://raw.githubusercontent.com/berkay-digital/Proxy-Scraper/refs/heads/main/proxies.txt',
        # 'https://github.com/XigmaDev/proxy/raw/refs/heads/main/proxies.txt',
        # 'https://github.com/chekamarue/proxies/raw/refs/heads/main/https.txt',
        # 'https://github.com/chekamarue/proxies/raw/refs/heads/main/httpss.txt',
        # 'https://github.com/claude89757/free_https_proxies/raw/refs/heads/main/https_proxies.txt',
        # 'https://github.com/claude89757/free_https_proxies/raw/refs/heads/main/isz_https_proxies.txt',
        # 'https://raw.githubusercontent.com/joy-deploy/free-proxy-list/refs/heads/main/data/latest/types/http/proxies.txt',
        # 'https://github.com/andigwandi/free-proxy/raw/refs/heads/main/proxy_list.txt',
        # 'https://raw.githubusercontent.com/parserpp/ip_ports/refs/heads/main/proxyinfo.txt',
        # 'https://raw.githubusercontent.com/Firmfox/Proxify/refs/heads/main/proxies/http.txt',
        # 'https://raw.githubusercontent.com/ebrasha/abdal-proxy-hub/refs/heads/main/http-proxy-list-by-EbraSha.txt',
        # 'https://rootjazz.com/proxies/proxies.txt',
        # 'https://api.proxyscrape.com/v3/free-proxy-list/get?request=displayproxies&protocol=http&proxy_format=ipport&format=text&timeout=20000',
        # 'https://proxyspace.pro/http.txt',
    )

    # Light endpoints to quickly check if proxy works
    _HTTP_TEST_URL: str = "http://example.com/"
    _HTTPS_TEST_URL: str = "https://www.google.com/generate_204"

    # Used to detect transparent proxies
    _PROXY_TEST_IP: str = "http://httpbin.org/ip"
    _ECHO_URL: str = "http://httpbin.org/anything"

    # Common headers that may reveal proxy usage
    _LEAK_HEADERS: Set[str] = {"via", "forwarded", "x-forwarded-for", "x-real-ip", "client-ip"}

    _SERVICE_URLS: Dict[str, str] = {
        "latency": "https://www.google.com/generate_204",
        "cloudflare": "https://www.cloudflare.com/cdn-cgi/trace",
        "youtube": "https://www.youtube.com/",
        "github": "https://api.github.com/",
        "bing": "https://www.bing.com/",
    }

    def __init__(
        self,
        *,
        src_concurrency: int = 15,
        proxy_concurrency: int = 200,
        quality_concurrency: int = 50,
        batch_size: int = 10000,
        request_timeout_total: int = 20,
        log_level: int = logging.INFO,
    ) -> None:
        """Advanced settings (not recommended to change)"""
        self._src_concurrency = src_concurrency
        self._proxy_concurrency = proxy_concurrency
        self._quality_concurrency = quality_concurrency
        self._batch_size = batch_size
        self._request_timeout_total = request_timeout_total

        logging.basicConfig(level=log_level, format="%(levelname)s: %(message)s")
        self._log = logging.getLogger("proxydog")

    def run(self, *, save_path: Optional[str] = "proxies.json") -> List[ProxyQuality]:
        """Runs full pipeline and optionally saves JSON"""
        result = asyncio.run(self._run_async())
        if save_path:
            self.save_json(result, save_path)
        return result

    def _chunked(self, seq: Sequence[str], size: int) -> Iterable[Sequence[str]]:
        """Split list into chunks to avoid task flooding"""
        for i in range(0, len(seq), size):
            yield seq[i : i + size]

    async def _get_proxies(self, session: aiohttp.ClientSession, sem: asyncio.Semaphore, url: str) -> Set[str]:
        """Fetch and parse proxies from a single source in the form ip:port"""
        result: Set[str] = set()
        try:
            async with sem:
                async with session.get(url) as response:
                    if response.ok:
                        resp = await response.text(errors="ignore")
                        for line in resp.strip().split("\n"):
                            line = line.strip()
                            if not line:
                                continue

                            # Some sources include full URLs.
                            line = line.removeprefix("http://").removeprefix("https://")

                            parts = line.split(":")
                            if len(parts) >= 2:
                                ip, port = parts[0], parts[1]
                                if port.isdigit():
                                    result.add(f"{ip}:{port}")
        except Exception:
            # Sources may fail or get into rate-limit
            self._log.debug("Source fetch failed: %s", url)
        return result

    async def _proxy_is_alive(
        self,
        session: aiohttp.ClientSession,
        proxy: str,
        *,
        timeout: int = 6,
        to_check: str,
    ) -> bool:
        """proxy should respond to GET"""
        try:
            async with session.get(
                    to_check,
                    proxy=f"http://{proxy}",
                    timeout=aiohttp.ClientTimeout(total=timeout),
                    allow_redirects=True,
            ) as response:
                if response.status in (403, 429):
                    await asyncio.sleep(0.2 + random.random() * 0.3)
                    return False
                return 200 <= response.status < 400
        except Exception:
            # Add small jitter to prevent a tight failure loop at high concurrency
            await asyncio.sleep(0.05 + random.random() * 0.1)
            return False

    async def _get_seen_ip(
        self,
        session: aiohttp.ClientSession,
        *,
        proxy: Optional[str] = None,
        timeout: int = 6,
    ) -> Optional[str]:
        """Get external IP without proxy for transparency check"""
        kwargs: Dict[str, Any] = {"timeout": aiohttp.ClientTimeout(total=timeout)}
        if proxy:
            kwargs["proxy"] = f"http://{proxy}"
        async with session.get(self._PROXY_TEST_IP, **kwargs) as response:
            data: Dict[str, Any] = await response.json(content_type=None)
            return data.get("origin")

    async def _check_anonymity(
        self,
        session: aiohttp.ClientSession,
        proxy: str,
        *,
        my_ip: Optional[str],
        timeout: int = 6,
    ) -> str:
        """Rough anonymity check based on echoed IP/headers"""
        try:
            async with session.get(
                self._ECHO_URL,
                proxy=f"http://{proxy}",
                timeout=aiohttp.ClientTimeout(total=timeout),
                allow_redirects=True,
            ) as resp:
                data: Dict[str, Any] = await resp.json(content_type=None)
        except (asyncio.TimeoutError, aiohttp.ClientError):
            # caller will drop the proxy.
            return "transparent"
        except Exception:
            return "transparent"

        origin = str(data.get("origin", ""))
        headers = {str(k).lower() for k in (data.get("headers") or {}).keys()}

        if my_ip and my_ip in origin:
            return "transparent"
        if headers & self._LEAK_HEADERS:
            return "anonymous"
        return "elite"

    async def _check_proxy(
        self,
        session: aiohttp.ClientSession,
        sem: asyncio.Semaphore,
        proxy: str,
        *,
        my_ip: Optional[str],
    ) -> Optional[str]:
        """Primary filter: HTTP ok + HTTPS ok + not transparent"""
        async with sem:
            try:
                if not await self._proxy_is_alive(session, proxy, to_check=self._HTTP_TEST_URL):
                    return None
                if not await self._proxy_is_alive(session, proxy, to_check=self._HTTPS_TEST_URL):
                    return None

                anonymity = await self._check_anonymity(session, proxy, my_ip=my_ip)
                if anonymity == "transparent":
                    return None

                return proxy
            except (asyncio.TimeoutError, aiohttp.ClientError):
                return None

    async def _fetch_check(
        self,
        session: aiohttp.ClientSession,
        proxy: str,
        url: str,
        *,
        timeout: int = 6,
        read_limit: int = 8192,
    ) -> Dict[str, Any]:
        """Request through proxy with latency measurement"""
        t0 = time.perf_counter()
        try:
            async with session.get(
                url,
                proxy=f"http://{proxy}",
                timeout=aiohttp.ClientTimeout(total=timeout),
                allow_redirects=True,
            ) as resp:
                await resp.content.read(read_limit)
                ms = int((time.perf_counter() - t0) * 1000)
                return {"ok": 200 <= resp.status < 400, "status": resp.status, "latency_ms": ms}
        except Exception as e:
            ms = int((time.perf_counter() - t0) * 1000)
            return {"ok": False, "status": 0, "latency_ms": ms, "error": type(e).__name__}

    async def _measure_latency(self, session: aiohttp.ClientSession, proxy: str, *, tries: int = 3) -> Optional[int]:
        """Median of a few samples to reduce spikes"""
        samples: List[int] = []
        for _ in range(tries):
            res = await self._fetch_check(session, proxy, self._SERVICE_URLS["latency"])
            if not res["ok"]:
                return None
            samples.append(int(res["latency_ms"]))

        samples.sort()
        return samples[len(samples) // 2]

    async def _check_services(self, session: aiohttp.ClientSession, proxy: str) -> Dict[str, Dict[str, Any]]:
        results: Dict[str, Dict[str, Any]] = {}
        for name, url in self._SERVICE_URLS.items():
            if name == "latency":
                continue
            results[name] = await self._fetch_check(session, proxy, url)
        return results

    async def _check_proxy_quality(
        self,
        session: aiohttp.ClientSession,
        sem: asyncio.Semaphore,
        proxy: str,
    ) -> Optional[ProxyQuality]:
        """Secondary filter: latency + a few real websites"""
        async with sem:
            latency = await self._measure_latency(session, proxy)
            if latency is None:
                return None

            services = await self._check_services(session, proxy)
            ok_services = sum(1 for r in services.values() if r["ok"])

            if latency > 6000:
                return None
            if ok_services < 3:
                return None

            return ProxyQuality(proxy=proxy, latency_ms=latency, services_ok=ok_services, services=services)

    async def _run_async(self) -> List[ProxyQuality]:
        connector = aiohttp.TCPConnector(
            limit=self._proxy_concurrency + self._quality_concurrency,
            limit_per_host=0,
            ttl_dns_cache=300,
        )
        async with aiohttp.ClientSession(connector=connector) as session:
            src_sem = asyncio.Semaphore(self._src_concurrency)

            collected = await tqdm_asyncio.gather(
                *(self._get_proxies(session, src_sem, s) for s in self._SOURCES),
                desc="Collecting",
                total=len(self._SOURCES),
                unit="sources",
                leave=True,
                dynamic_ncols=True,
            )

            raw_proxies: Set[str] = set()
            for proxy_set in collected:
                if isinstance(proxy_set, Exception):
                    continue
                raw_proxies.update(proxy_set)
            raw_list: Tuple[str, ...] = tuple(raw_proxies)

            my_ip = await self._get_seen_ip(session)
            self._log.info("Collected proxies: %d", len(raw_list))

            p_sem = asyncio.Semaphore(self._proxy_concurrency)

            filtered: List[str] = []
            for batch in self._chunked(raw_list, self._batch_size):
                batch_checked = await tqdm_asyncio.gather(
                    *(self._check_proxy(session, p_sem, proxy, my_ip=my_ip) for proxy in batch),
                    desc="Primary filtering",
                    total=len(batch),
                    unit="proxies",
                    dynamic_ncols=True,
                    mininterval=0.2,
                    smoothing=0.1,
                    leave=False,
                    bar_format="{l_bar}{bar} | {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]",
                )

                res = [p for p in batch_checked if isinstance(p, str) and p]
                self._log.info("Batch finish: %d passed", len(res))
                filtered.extend(res)

            self._log.info("After primary filter: %d passed", len(filtered))

            q_sem = asyncio.Semaphore(self._quality_concurrency)
            quality = await tqdm_asyncio.gather(
                *(self._check_proxy_quality(session, q_sem, proxy) for proxy in filtered),
                desc="Quality filtering",
                total=len(filtered),
                unit="proxies",
                dynamic_ncols=True,
                mininterval=0.2,
                smoothing=0.1,
                leave=True,
            )

            final = [r for r in quality if isinstance(r, ProxyQuality)]
            final.sort(key=lambda x: (-x.services_ok, x.latency_ms))

            self._log.info("Final proxies: %d", len(final))
            return final

    def save_json(self, items: Sequence[ProxyQuality], path: str = "proxies.json") -> None:
        """Save results to JSON"""
        payload = [
            {
                "proxy": i.proxy,
                "latency_ms": i.latency_ms,
                "services_ok": i.services_ok,
                "services": i.services,
            }
            for i in items
        ]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)


def _main() -> None:
    ProxyDog().run(save_path="proxies.json")



if __name__ == "__main__":
    _main()
