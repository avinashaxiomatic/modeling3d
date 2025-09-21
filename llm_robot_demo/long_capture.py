import os
import json
import math
import time
import requests


BASE = "http://127.0.0.1:5001"


def get(path):
    r = requests.get(f"{BASE}{path}")
    r.raise_for_status()
    return r.json()


def post(path, payload):
    r = requests.post(
        f"{BASE}{path}",
        headers={"Content-Type": "application/json"},
        data=json.dumps(payload),
    )
    r.raise_for_status()
    return r.json()


def linspace(a, b, n):
    for i in range(n):
        t = i / (n - 1) if n > 1 else 1.0
        yield [(1 - t) * x + t * y for x, y in zip(a, b)]


def main():
    # Ensure frames directory exists
    os.makedirs("frames", exist_ok=True)

    # Current pose
    current = get("/state")["joints"]

    # Define a few waypoints to make motion interesting
    waypoints = [
        current,
        [current[0] + 0.3, -0.5, 0.1, -1.6, 0.0, 1.4, 0.6],
        [current[0] - 0.3, -0.4, -0.1, -1.9, 0.0, 1.8, 0.9],
        [current[0], -0.3, 0.0, -1.8, 0.0, 1.6, 0.7],
    ]

    total_frames = 150  # ~5 seconds at 30 fps
    segments = len(waypoints) - 1
    frames_per_segment = max(1, total_frames // segments)

    frame_idx = 1
    for seg in range(segments):
        a = waypoints[seg]
        b = waypoints[seg + 1]
        for q in linspace(a, b, frames_per_segment):
            # quick move and capture
            post("/movej", {"targets": q, "duration": 0.02})
            out = os.path.join("frames", f"frame_{frame_idx:04d}.png")
            post("/snapshot", {"path": out})
            frame_idx += 1
            # tiny pacing to avoid HTTP pileup
            time.sleep(0.005)

    print(f"saved {frame_idx-1} frames under {os.path.abspath('frames')}")


if __name__ == "__main__":
    main()


