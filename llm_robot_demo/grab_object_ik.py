import os
import json
import time
import math
from typing import List

import requests
import imageio.v2 as imageio


BASE = "http://127.0.0.1:5001"
H = {"Content-Type": "application/json"}


def get(path: str):
    r = requests.get(f"{BASE}{path}")
    r.raise_for_status()
    return r.json()


def post(path: str, payload: dict):
    r = requests.post(f"{BASE}{path}", headers=H, data=json.dumps(payload))
    r.raise_for_status()
    return r.json()


def ee_cube_distance() -> float:
    d = get("/poses")
    ee = d["ee"]["pos"]
    cb = d["cube"]["pos"]
    if ee is None or cb is None:
        return float("inf")
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(ee, cb)))


def snapshot(folder: str, idx: int):
    os.makedirs(folder, exist_ok=True)
    fn = os.path.join(folder, f"grab_{idx:04d}.png")
    post("/snapshot", {"path": fn})
    return fn


def encode_video(frames: List[str], out_path: str, fps: int = 10):
    imgs = [imageio.imread(f) for f in frames]
    imageio.mimsave(out_path, imgs, fps=fps, codec="libx264")


def main():
    frames_dir = "frames_grab"
    frames: List[str] = []
    idx = 1

    # Ensure cube present
    post("/spawn_cube", {"pos": [0.55, 0.0, 0.025]})
    cube = get("/poses")["cube"]["pos"]

    # Home pose
    A = [0.0, -0.4, 0.0, -2.0, 0.0, 1.7, 0.8]
    post("/movej", {"targets": A, "duration": 0.6})
    frames.append(snapshot(frames_dir, idx)); idx += 1

    # Pre-grasp: 5 cm above the cube, slightly offset in -x
    pre = [cube[0] - 0.03, cube[1], cube[2] + 0.05]
    post("/move_ik", {"pos": pre, "duration": 1.2})
    frames.append(snapshot(frames_dir, idx)); idx += 1

    # Approach straight down to 1 cm above
    approach = [cube[0] - 0.01, cube[1], cube[2] + 0.01]
    post("/move_ik", {"pos": approach, "duration": 1.0})
    frames.append(snapshot(frames_dir, idx)); idx += 1

    # Close gripper without auto-attach
    post("/gripper_raw", {"width": 0.0})
    frames.append(snapshot(frames_dir, idx)); idx += 1

    # If very close, attach rigidly; else leave as is (no snapping)
    if ee_cube_distance() < 0.02:
        post("/force_grasp", {})
    frames.append(snapshot(frames_dir, idx)); idx += 1

    # Lift 10 cm
    lift = [approach[0], approach[1], cube[2] + 0.11]
    post("/move_ik", {"pos": lift, "duration": 1.2})
    frames.append(snapshot(frames_dir, idx)); idx += 1

    # Encode video
    out_video = "grab_ik.mp4"
    encode_video(frames, out_video, fps=10)

    print("frames_dir", os.path.abspath(frames_dir))
    print("video", os.path.abspath(out_video))


if __name__ == "__main__":
    main()


