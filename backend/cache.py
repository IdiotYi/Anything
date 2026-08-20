"""Small thread-safe TTL cache for the single-process demo server."""

import threading
import time


class TTLCache:
    def __init__(self, ttl_seconds, max_entries):
        self.ttl_seconds = ttl_seconds
        self.max_entries = max_entries
        self._entries = {}
        self._lock = threading.Lock()

    def get(self, key):
        now = time.monotonic()
        with self._lock:
            entry = self._entries.get(key)
            if entry is None:
                return None
            expires_at, value = entry
            if expires_at <= now:
                self._entries.pop(key, None)
                return None
            return value

    def set(self, key, value, ttl_seconds=None):
        now = time.monotonic()
        ttl = self.ttl_seconds if ttl_seconds is None else ttl_seconds
        with self._lock:
            self._discard_expired(now)
            if key not in self._entries and len(self._entries) >= self.max_entries:
                oldest_key = min(self._entries, key=lambda item: self._entries[item][0])
                self._entries.pop(oldest_key, None)
            self._entries[key] = (now + ttl, value)

    def clear(self):
        with self._lock:
            self._entries.clear()

    def _discard_expired(self, now):
        expired = [key for key, (expires_at, _) in self._entries.items() if expires_at <= now]
        for key in expired:
            self._entries.pop(key, None)
