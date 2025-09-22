import os
import json
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


def save_frame(folder: str, idx: int) -> str:
    os.makedirs(folder, exist_ok=True)
    fn = os.path.join(folder, f"mg_{idx:04d}.png")
    post("/snapshot", {"path": fn})
    return fn


def encode(frames: List[str], out_path: str, fps: int = 6):
    imgs = [imageio.imread(f) for f in frames]
    imageio.mimsave(out_path, imgs, fps=fps, codec="libx264")


def main():
    frames_dir = "frames_move_grabbed"
    frames: List[str] = []
    idx = 1

    # Ensure cube exists and go home
    post("/spawn_cube", {"pos": [0.55, 0.0, 0.025]})
    A = [0.0, -0.4, 0.0, -2.0, 0.0, 1.7, 0.8]
    post("/movej", {"targets": A, "duration": 0.6})
    frames.append(save_frame(frames_dir, idx)); idx += 1

    # Pre-grasp above cube
    cb = get("/poses")["cube"]["pos"]
    pre = [cb[0] - 0.02, cb[1], cb[2] + 0.05]
    post("/move_ik", {"pos": pre, "duration": 1.2})
    frames.append(save_frame(frames_dir, idx)); idx += 1

    # Approach near the cube
    approach = [cb[0] - 0.005, cb[1], cb[2] + 0.01]
    post("/move_ik", {"pos": approach, "duration": 1.0})
    frames.append(save_frame(frames_dir, idx)); idx += 1

    # Close gripper (no auto attach), then attach if very close
    post("/gripper_raw", {"width": 0.0})
    if ee_cube_distance() < 0.02:
        post("/force_grasp", {})
    frames.append(save_frame(frames_dir, idx)); idx += 1

    # Move the grabbed object to a new location (translate +0.25 in x and +0.18 in y, lift to +0.12)
    target = [cb[0] + 0.25, cb[1] + 0.18, cb[2] + 0.12]
    post("/move_ik", {"pos": target, "duration": 2.0})
    frames.append(save_frame(frames_dir, idx)); idx += 1

    # Hold pose
    frames.append(save_frame(frames_dir, idx)); idx += 1

    out_video = "move_grabbed.mp4"
    encode(frames, out_video, fps=6)
    print("frames_dir", os.path.abspath(frames_dir))
    print("video", os.path.abspath(out_video))


if __name__ == "__main__":
    main()


