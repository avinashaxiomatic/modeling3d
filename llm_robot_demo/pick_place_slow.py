import os
import json
import time
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


def get(path):
    r = requests.get(f"{BASE}{path}")
    r.raise_for_status()
    return r.json()


def lerp(a, b, t):
    return [(1 - t) * x + t * y for x, y in zip(a, b)]


def capture_frame(idx: int, tag: str = ""):
    name = f"pp_{idx:04d}.png" if not tag else f"pp_{tag}_{idx:04d}.png"
    out = os.path.join("frames", name)
    post("/snapshot", {"path": out})


def main():
    os.makedirs("frames", exist_ok=True)

    # Prep: open gripper, spawn cube, go home
    post("/gripper", {"width": 0.08})
    post("/spawn_cube", {"pos": [0.55, 0.0, 0.025]})

    home = [0, -0.4, 0, -2.0, 0, 1.7, 0.8]
    pre = [0.0, -0.6, 0.0, -1.8, 0.0, 1.7, 0.6]
    lift = [0.0, -0.5, 0.0, -1.6, 0.0, 1.5, 0.6]
    place = [0.3, -0.5, 0.0, -1.7, 0.0, 1.6, 0.7]

    idx = 1
    frames_per_segment = 24  # even smoother

    def smoothstep(x: float) -> float:
        # ease-in-out (cubic)
        return 3 * x * x - 2 * x * x * x

    # Home frame
    post("/movej", {"targets": home, "duration": 0.8})
    # preroll hold at home
    for _ in range(10):
        capture_frame(idx); idx += 1

    # Move: home -> pre-grasp
    for k in range(frames_per_segment + 8):
        t = (k + 1) / frames_per_segment
        q = lerp(home, pre, smoothstep(t))
        post("/movej", {"targets": q, "duration": 0.04})
        capture_frame(idx); idx += 1

    # Align cube right under EE for a visible grasp
    post("/align_cube_to_ee", {"offset": [0, 0, -0.06]})
    capture_frame(idx); idx += 1

    # GRIP event: close slowly + hold a few frames
    post("/gripper", {"width": 0.0})
    # Ensure rigid attach
    post("/force_grasp", {})
    for _ in range(10):
        capture_frame(idx, tag="grip"); idx += 1

    # Move: pre-grasp -> lift
    for k in range(frames_per_segment + 8):
        t = (k + 1) / frames_per_segment
        q = lerp(pre, lift, smoothstep(t))
        post("/movej", {"targets": q, "duration": 0.04})
        capture_frame(idx); idx += 1

    # Move: lift -> place
    for k in range(frames_per_segment + 8):
        t = (k + 1) / frames_per_segment
        q = lerp(lift, place, smoothstep(t))
        post("/movej", {"targets": q, "duration": 0.05})
        capture_frame(idx); idx += 1

    # RELEASE event + hold frames
    post("/release", {})
    for _ in range(10):
        capture_frame(idx, tag="release"); idx += 1

    # Move: place -> home
    for k in range(frames_per_segment + 8):
        t = (k + 1) / frames_per_segment
        q = lerp(place, home, smoothstep(t))
        post("/movej", {"targets": q, "duration": 0.04})
        capture_frame(idx); idx += 1

    # postroll hold at home
    for _ in range(10):
        capture_frame(idx); idx += 1

    print(f"saved {idx-1} frames under {os.path.abspath('frames')}")


if __name__ == "__main__":
    main()


