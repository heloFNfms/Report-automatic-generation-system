import os, json
try:
    import redis  # type: ignore
except Exception:
    redis = None

class Cache:
    def __init__(self):
        self.url = os.getenv("REDIS_URL")
        self.ttl = int(os.getenv("CACHE_TTL", "3600"))
        self.client = None
        if self.url and redis is not None:
            try:
                self.client = redis.from_url(self.url)
                self.client.ping()
            except Exception:
                self.client = None
        self._mem = {}

    def get(self, key):
        try:
            if self.client:
                v = self.client.get(key)
                return json.loads(v) if v else None
            return self._mem.get(key)
        except Exception:
            return None

    def set(self, key, value):
        try:
            if self.client:
                self.client.setex(key, self.ttl, json.dumps(value, ensure_ascii=False))
            else:
                self._mem[key] = value
        except Exception:
            pass

