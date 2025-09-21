import os
import json
import time
import math
from typing import List, Tuple

import requests


BASE = "http://127.0.0.1:5001"


def get(path):
    r = requests.get(f"{BASE}{path}")
    r.raise_for_status()
    return r.json()


def post(path, payload):
    r = requests.post(
        f"{BASE}{path}", headers={"Content-Type": "application/json"}, data=json.dumps(payload)
    )
    r.raise_for_status()
    return r.json()


def distance_ee_to_cube() -> float:
    d = get("/poses")
    ee = d["ee"]["pos"]
    cb = d["cube"]["pos"]
    if ee is None or cb is None:
        return float("inf")
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(ee, cb)))


def movej(q: List[float], dur: float = 0.1):
    post("/movej", {"targets": q, "duration": dur})


def snapshot(frames_dir: str, idx: int):
    os.makedirs(frames_dir, exist_ok=True)
    out = os.path.join(frames_dir, f"ns_{idx:04d}.png")
    post("/snapshot", {"path": out})


def local_refine_around(q_base: List[float]) -> List[float]:
    # Small local search around q_base (adjust 3 joints) to minimize EE-cube distance without snapping
    candidates: List[Tuple[float, List[float]]] = []
    deltas = [-0.12, -0.06, -0.02, 0.0, 0.02, 0.06, 0.12]
    test_joints = [1, 3, 6]  # empirically influential
    best_q = q_base[:]
    best_d = distance_ee_to_cube()
    for d1 in deltas:
        for d2 in deltas:
            for d3 in deltas:
                q = q_base[:]
                q[test_joints[0]] += d1
                q[test_joints[1]] += d2
                q[test_joints[2]] += d3
                movej(q, 0.05)
                d = distance_ee_to_cube()
                candidates.append((d, q))
                if d < best_d:
                    best_d, best_q = d, q[:]
    # move to best pose once
    movej(best_q, 0.08)
    return best_q


def main():
    frames_dir = "frames_no_snap"
    idx = 1

    # Setup scene
    post("/gripper", {"width": 0.08})
    post("/spawn_cube", {"pos": [0.55, 0.0, 0.025]})

    # Waypoints (reuse previous ones to get near the cube)
    home = [0, -0.4, 0, -2.0, 0, 1.7, 0.8]
    pre = [0.0, -0.6, 0.0, -1.8, 0.0, 1.7, 0.6]
    lift = [0.0, -0.5, 0.0, -1.6, 0.0, 1.5, 0.6]
    place = [0.3, -0.5, 0.0, -1.7, 0.0, 1.6, 0.7]

    movej(home, 0.6); snapshot(frames_dir, idx); idx += 1
    movej(pre, 0.8); snapshot(frames_dir, idx); idx += 1

    # Refine locally to get within grasp threshold (no snapping)
    q_curr = get("/state")["joints"]
    q_best = local_refine_around(q_curr)
    snapshot(frames_dir, idx); idx += 1

    # Close gripper raw (no auto-attach)
    post("/gripper_raw", {"width": 0.0})
    snapshot(frames_dir, idx); idx += 1

    # Attempt attach only if within threshold (no snapping). If not close, do NOT attach.
    if distance_ee_to_cube() < 0.08:
        post("/force_grasp", {})
    snapshot(frames_dir, idx); idx += 1

    # Lift and place sequence
    movej(lift, 0.8); snapshot(frames_dir, idx); idx += 1
    movej(place, 1.0); snapshot(frames_dir, idx); idx += 1

    # Release
    post("/release", {})
    snapshot(frames_dir, idx); idx += 1

    # Home
    movej(home, 0.8)
    snapshot(frames_dir, idx); idx += 1

    print("saved frames to:", os.path.abspath(frames_dir))


if __name__ == "__main__":
    main()


