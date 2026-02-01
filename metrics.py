from collections import Counter
from threading import Lock
from typing import Dict, Optional

_lock = Lock()
_counters = Counter()


def increment(name: str, labels: Optional[Dict[str, str]] = None) -> None:
    key = name
    if labels:
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        key = f"{name}|{label_str}"
    with _lock:
        _counters[key] += 1


def snapshot() -> Dict[str, int]:
    with _lock:
        return dict(_counters)

