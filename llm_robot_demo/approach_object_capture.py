import os
import json
import time
import math
from typing import List, Tuple

import requests


BASE = "http://127.0.0.1:5001"


def get(path: str):
    r = requests.get(f"{BASE}{path}")
    r.raise_for_status()
    return r.json()


def post(path: str, payload: dict):
    r = requests.post(
        f"{BASE}{path}", headers={"Content-Type": "application/json"}, data=json.dumps(payload)
    )
    r.raise_for_status()
    return r.json()


def ee_cube_distance() -> float:
    d = get("/poses")
    ee = d["ee"]["pos"]
    cb = d["cube"]["pos"]
    if ee is None or cb is None:
        return float("inf")
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(ee, cb)))


def movej(q: List[float], duration: float = 0.05):
    post("/movej", {"targets": q, "duration": duration})


def snapshot(folder: str, idx: int):
    os.makedirs(folder, exist_ok=True)
    out = os.path.join(folder, f"ap_{idx:04d}.png")
    post("/snapshot", {"path": out})


def local_descent(q_start: List[float], max_iters: int = 80) -> List[float]:
    q = q_start[:]
    # Small joint indices that have large effect on EE pose
    joint_ids = [0, 1, 3, 6]
    step = 0.04
    best = ee_cube_distance()
    for _ in range(max_iters):
        improved = False
        for j in joint_ids:
            for s in (+step, -step):
                q_try = q[:]
                q_try[j] += s
                movej(q_try, 0.04)
                d = ee_cube_distance()
                if d < best:
                    q = q_try
                    best = d
                    improved = True
        if not improved:
            step *= 0.5
            if step < 0.005:
                break
    return q


def main():
    frames_dir = "frames_approach"
    idx = 1

    # Ensure cube exists near (0.55, 0, 0.025)
    post("/spawn_cube", {"pos": [0.55, 0.0, 0.025]})

    # Start configuration A
    A = [0.0, -0.4, 0.0, -2.0, 0.0, 1.7, 0.8]
    movej(A, 0.6)
    snapshot(frames_dir, idx); idx += 1

    # Coarse move toward the object (heuristic pose)
    coarse = [0.2, -0.55, 0.1, -1.7, 0.0, 1.5, 0.65]
    movej(coarse, 0.6)
    snapshot(frames_dir, idx); idx += 1

    # Local descent to get close (no grabbing)
    q_curr = get("/state")["joints"]
    q_final = local_descent(q_curr, max_iters=120)
    snapshot(frames_dir, idx); idx += 1

    print("final_distance_m:", round(ee_cube_distance(), 4))
    print("saved frames in:", os.path.abspath(frames_dir))


if __name__ == "__main__":
    main()


