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


def get_state():
    return requests.get(f"{BASE}/state").json()["joints"]


def main():
    os.makedirs("frames", exist_ok=True)

    # Reset-ish: open gripper and spawn cube
    post("/gripper", {"width": 0.08})
    post("/spawn_cube", {"pos": [0.55, 0.0, 0.025]})

    # Home-ish
    home = [0, -0.4, 0, -2.0, 0, 1.7, 0.8]
    post("/movej", {"targets": home, "duration": 1.0})
    post("/snapshot", {"path": os.path.join("frames", "pp_0001.png")})

    # Approach cube
    pre_grasp = [0.0, -0.6, 0.0, -1.8, 0.0, 1.7, 0.6]
    post("/movej", {"targets": pre_grasp, "duration": 1.0})
    # Snap-align cube directly under the end-effector to ensure visible grasp
    post("/align_cube_to_ee", {"offset": [0, 0, -0.08]})
    post("/snapshot", {"path": os.path.join("frames", "pp_0002.png")})

    # Close gripper -> latch constraint if close enough
    post("/gripper", {"width": 0.0})
    post("/snapshot", {"path": os.path.join("frames", "pp_0003.png")})

    # Lift
    lift = [0.0, -0.5, 0.0, -1.6, 0.0, 1.5, 0.6]
    post("/movej", {"targets": lift, "duration": 1.0})
    post("/snapshot", {"path": os.path.join("frames", "pp_0004.png")})

    # Move to place pose
    place = [0.3, -0.5, 0.0, -1.7, 0.0, 1.6, 0.7]
    post("/movej", {"targets": place, "duration": 1.2})
    post("/snapshot", {"path": os.path.join("frames", "pp_0005.png")})

    # Release
    post("/release", {})
    post("/snapshot", {"path": os.path.join("frames", "pp_0006.png")})

    # Back to home
    post("/movej", {"targets": home, "duration": 1.0})
    post("/snapshot", {"path": os.path.join("frames", "pp_0007.png")})

    print("pick-and-place frames saved in:", os.path.abspath("frames"))


if __name__ == "__main__":
    main()


