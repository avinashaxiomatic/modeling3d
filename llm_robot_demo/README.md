# LLM → Robot Arm (software-only) demo

Minimal macOS-friendly demo showing a simulated Franka Panda arm controlled via REST.

## Quickstart

1) Create venv and install deps
```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2) Start the simulator REST server (opens a PyBullet GUI window)
```
python server.py
```

3) In a second terminal, move the arm
```
python client.py
```

- GET state: `curl http://127.0.0.1:5001/state`
- POST movej:
```
curl -X POST http://127.0.0.1:5001/movej \
  -H 'Content-Type: application/json' \
  -d '{"targets":[0,-0.3,0,-1.8,0,1.6,0.7],"duration":3.0}'
```

## Next steps
- Swap PyBullet for Isaac Sim Kit + REST (kit-automation-sample) for Omniverse-native control.
- Add IK, waypoints, and gripper open/close.
- Record a 60–90s video of natural-language commands driving motions.
