import json
import time
from typing import List

import requests


def get_state(base: str = "http://127.0.0.1:5001"):
    r = requests.get(f"{base}/state")
    r.raise_for_status()
    return r.json()["joints"]


def movej(targets: List[float], duration: float = 2.0, base: str = "http://127.0.0.1:5001"):
    r = requests.post(
        f"{base}/movej",
        headers={"Content-Type": "application/json"},
        data=json.dumps({"targets": targets, "duration": duration}),
    )
    r.raise_for_status()
    return r.json()


if __name__ == "__main__":
    print("Current joints:", get_state())
    demo_pose = [0.0, -0.3, 0.0, -1.8, 0.0, 1.6, 0.7]
    print("Moving to demo pose...")
    print(movej(demo_pose, duration=3.0))
    time.sleep(0.5)
    print("Done. Current joints:", get_state())


