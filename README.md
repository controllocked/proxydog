# ProxyDog 🐶


A small asynchronous utility to collect public HTTP proxies from open sources and filter them in 2 steps:

1. **Primary filtering**: checks that a proxy responds to a simple HTTP request and can also reach an HTTPS URL. Also removes **transparent** proxies.
2. **Quality filtering**: measures latency and checks a few popular websites.

> Public proxy lists are usually low quality, so the final amount of working proxies can be small.

## What it does

- Downloads proxy lists from multiple URLs.
- Normalizes entries to `ip:port`.
- Primary checks:
  - HTTP: `http://example.com/`
  - HTTPS: `https://www.google.com/generate_204`
- Anonymity check via `http://httpbin.org/anything`:
  - `transparent` - removed
  - `anonymous` / `elite` - kept
- Quality checks:
  - median latency using `generate_204`
  - availability of: Cloudflare / YouTube / GitHub / Bing

Results are saved to the JSON file.

## Demonstration

![Demonstration](/demo.gif?raw=true "Demo")


## Install

Requirements:

- Python 3.10+ (recommended)
- Install everything listed in requirements.txt

Example:

```bash
pip install -r requirements.txt
```

## Run

```bash
python3 proxydog.py
```

After completion you will get `proxies.json` by default.

## Settings

Main options are in `ProxyDog()` constructor:

- `src_concurrency` - parallel downloads of sources
- `proxy_concurrency` - parallel primary checks
- `quality_concurrency` - parallel quality checks
- `batch_size` - chunk size (prevents creating too many tasks at once)
- `request_timeout_total` - total session timeout

> It is not recommended to change them (unless you know what you are doing).
## Notes

- Public proxies are unstable.
- Some endpoints may rate-limit/block proxy traffic.
- If progress looks stuck, it is usually waiting for timeouts on slow/broken proxies.
- If the progress, on the contrary, seems inadequately fast, try to reduce the number of Sources. 
## License

This project is licensed under the MIT License.  
See the [LICENSE](LICENSE) file for details.

