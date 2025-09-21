import os
import json
import time
from typing import List

import requests


BASE = "http://127.0.0.1:5001"


def post(path, payload):
    r = requests.post(
        f"{BASE}{path}",
        headers={"Content-Type": "application/json"},
        data=json.dumps(payload),
    )
    r.raise_for_status()
    return r.json()


def linspace(a: List[float], b: List[float], n: int):
    for i in range(n):
        t = i / (n - 1) if n > 1 else 1.0
        yield [(1 - t) * x + t * y for x, y in zip(a, b)]


def snapshot(path: str):
    post("/snapshot", {"path": path})


def main():
    out_dir = "frames_simple"
    os.makedirs(out_dir, exist_ok=True)

    # Two simple poses (A -> B -> A)
    A = [0.0, -0.4, 0.0, -2.0, 0.0, 1.7, 0.8]
    B = [0.6, -0.6, 0.2, -1.6, 0.0, 1.3, 0.6]

    seq = [A, B, A]
    idx = 1
    steps_per_segment = 60

    # Start at A
    post("/movej", {"targets": A, "duration": 0.6})
    snapshot(os.path.join(out_dir, f"sm_{idx:04d}.png")); idx += 1

    for i in range(len(seq) - 1):
        a = seq[i]
        b = seq[i + 1]
        for q in linspace(a, b, steps_per_segment):
            post("/movej", {"targets": q, "duration": 0.03})
            snapshot(os.path.join(out_dir, f"sm_{idx:04d}.png")); idx += 1
            time.sleep(0.002)

    print("saved", idx - 1, "frames in", os.path.abspath(out_dir))


if __name__ == "__main__":
    main()


