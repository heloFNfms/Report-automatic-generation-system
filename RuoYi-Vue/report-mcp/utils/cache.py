import os
import redis
import json


class Cache:
    def __init__(self):
        url = os.getenv('REDIS_URL')
        self.ttl = int(os.getenv('CACHE_TTL', '3600'))
        self.client = None
        if url:
            try:
                self.client = redis.from_url(url)
                self.client.ping()
            except Exception:
                self.client = None
        self.mem = {}


    def get(self, key):
        try:
            if self.client:
                v = self.client.get(key)
                if v:
                    return json.loads(v)
            return self.mem.get(key)
        except Exception:
            return None


    def set(self, key, value):
        try:
            if self.client:
                self.client.setex(key, self.ttl, json.dumps(value, ensure_ascii=False))
            else:
                self.mem[key] = value
        except Exception:
            pass
