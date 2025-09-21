import json
import time
import requests


BASE = "http://127.0.0.1:5001"


def post(path, payload):
    r = requests.post(f"{BASE}{path}", headers={"Content-Type": "application/json"}, data=json.dumps(payload))
    r.raise_for_status()
    return r.json()


def main():
    poses = [
        [0.0, -0.3, 0.0, -1.8, 0.0, 1.6, 0.7],
        [0.2, -0.5, 0.1, -1.6, 0.0, 1.4, 0.6],
        [-0.2, -0.4, -0.1, -2.0, 0.0, 1.8, 0.8],
    ]
    for i, pose in enumerate(poses, start=1):
        post("/movej", {"targets": pose, "duration": 2.5})
        time.sleep(0.2)
        out = f"snapshot_{i}.png"
        post("/snapshot", {"path": out})
        print("saved", out)


if __name__ == "__main__":
    main()


