"""Fast outbound-connectivity check, run just before any generation that needs
to reach an external LLM provider (answer / fact / evaluation).

Why backend and not just the browser: the generation calls leave from *this*
process (the container), not the user's browser. navigator.onLine on the
frontend can say "online" while the container has no outbound access, which is
exactly how a fact-generation run started 103 provider calls with no internet
and produced a wall of error logs. Checking here, before the work is created,
stops that at the source.

Design goals (per request): run *before* the action, be *fast*, and only run
when we're about to hit an outside server.
- Fast: a single HTTP HEAD with a short timeout (default 3s). No LLM call, no
  cost. Cheap enough to run on every generation launch.
- Reliable-ish: we hit a couple of highly-available hosts and succeed if any
  responds. We only care "is there outbound internet at all", not which
  provider — a provider-specific failure (bad key, provider down) is a
  different error surfaced later with its own message.
- Safe default: any unexpected internal error in the check itself returns
  "reachable" so the check can never itself block a legitimate run; only a
  clean "all probes failed" returns offline.
"""
import logging
import socket
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

# Highly-available hosts. An HTTP response (even 4xx/3xx) proves connectivity;
# we only need the TCP+HTTP round-trip to complete, not a 200.
_PROBE_URLS = [
    'https://www.google.com/generate_204',   # returns 204, tiny, built for this
    'https://www.cloudflare.com/cdn-cgi/trace',
]


def check_internet(timeout: float = 3.0) -> bool:
    """Return True if outbound internet appears reachable, False if every probe
    fails. Never raises."""
    for url in _PROBE_URLS:
        try:
            req = Request(url, method='HEAD')
            # Any completed HTTP response (2xx/3xx/4xx) means we reached out.
            urlopen(req, timeout=timeout)
            return True
        except HTTPError:
            # We got an HTTP status back — that means connectivity is fine.
            return True
        except (URLError, socket.timeout, TimeoutError, OSError) as e:
            logging.debug(f"connectivity probe failed for {url}: {e}")
            continue
        except Exception as e:  # never let the check itself throw
            logging.debug(f"connectivity probe unexpected error for {url}: {e}")
            continue
    return False


# Standard error payload + status for endpoints to return when offline.
OFFLINE_STATUS = 503
OFFLINE_ERROR = {
    'error': 'No internet connection: the server cannot reach the model '
             'provider. Check the connection and try again.',
    'code': 'offline',
}
