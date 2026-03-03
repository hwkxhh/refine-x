"""Flush the Celery Redis queue and print all pending job IDs."""
import redis
import json

r = redis.from_url("redis://localhost:6379/0")
length = r.llen("celery")
print(f"Queue length before flush: {length}")
n = r.delete("celery")
print(f"Deleted 'celery' key: {n}")
print(f"Queue length after flush: {r.llen('celery')}")
