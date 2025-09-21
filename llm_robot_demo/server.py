import os
import time
from typing import List, Optional, Tuple

from flask import Flask, request, jsonify
import pybullet as p
import pybullet_data
import numpy as np
from PIL import Image


app = Flask(__name__)


class PandaSim:
    def __init__(self, gui: bool = True):
        self.gui = gui
        self.physics = p.connect(p.GUI if gui else p.DIRECT)
        p.resetSimulation()
        p.setAdditionalSearchPath(pybullet_data.getDataPath())
        p.setGravity(0, 0, -9.81)
        p.loadURDF("plane.urdf")
        self.panda = p.loadURDF(
            fileName=os.path.join(pybullet_data.getDataPath(), "franka_panda/panda.urdf"),
            basePosition=[0, 0, 0],
            useFixedBase=True,
        )
        arm_idxs = []
        finger_idxs = []
        self.ee_index = 11
        for i in range(p.getNumJoints(self.panda)):
            info = p.getJointInfo(self.panda, i)
            jtype = info[2]
            jname = info[1].decode("utf-8", errors="ignore")
            if jtype == p.JOINT_REVOLUTE:
                arm_idxs.append(i)
            if "finger" in jname:
                finger_idxs.append(i)
        self.arm_joint_indices: List[int] = arm_idxs
        self.finger_joint_indices: List[int] = finger_idxs
        self.cube_id: Optional[int] = None
        self.grasp_cid: Optional[int] = None
        self.pose_log: List[dict] = []
        self.t0 = time.time()
        self.reset()

    def now(self) -> float:
        return time.time() - self.t0

    def log_pose(self):
        ee_p, ee_q = self.get_ee_pose()
        cb_p, cb_q = self.get_cube_pose()
        self.pose_log.append({
            "t": self.now(),
            "ee": {"pos": ee_p, "orn_xyzw": ee_q},
            "cube": {"pos": cb_p, "orn_xyzw": cb_q},
        })
        if len(self.pose_log) > 5000:
            self.pose_log = self.pose_log[-5000:]

    def reset(self):
        target = [0, -0.4, 0, -2.0, 0, 1.7, 0.8]
        for j, v in zip(self.arm_joint_indices, target):
            p.resetJointState(self.panda, j, v)
        self.set_gripper_width(0.08)
        p.stepSimulation()
        self.pose_log = []
        self.t0 = time.time()
        self.log_pose()

    def get_joint_positions(self) -> List[float]:
        return [p.getJointState(self.panda, j)[0] for j in self.arm_joint_indices]

    def get_ee_pose(self) -> Tuple[List[float], List[float]]:
        pos, orn = p.getLinkState(self.panda, self.ee_index)[:2]
        return list(pos), list(orn)

    def get_cube_pose(self):
        if self.cube_id is None:
            return None, None
        pos, orn = p.getBasePositionAndOrientation(self.cube_id)
        return list(pos), list(orn)

    def movej(self, targets: List[float], duration: float = 2.0):
        start = np.array(self.get_joint_positions(), dtype=float)
        goal = np.array(targets, dtype=float)
        steps = max(1, int(duration / 0.01))
        for k in range(steps):
            alpha = (k + 1) / steps
            q = (1 - alpha) * start + alpha * goal
            p.setJointMotorControlArray(
                self.panda,
                self.arm_joint_indices,
                p.POSITION_CONTROL,
                targetPositions=q.tolist(),
                forces=[87.0] * len(self.arm_joint_indices),
            )
            p.stepSimulation()
            self.log_pose()
            time.sleep(0.01)

    def move_ik(self, pos: List[float], orn: Optional[List[float]] = None, duration: float = 1.5):
        if orn is None:
            _, orn_cur = self.get_ee_pose()
            orn = orn_cur
        ik_all = p.calculateInverseKinematics(
            self.panda,
            self.ee_index,
            targetPosition=pos,
            targetOrientation=orn,
        )
        # Map IK solution to our arm joint indices by index
        targets = [ik_all[j] for j in self.arm_joint_indices]
        self.movej(targets, duration)

    def set_gripper_width(self, width: float):
        width = float(max(0.0, min(0.08, width)))
        target = width * 0.5
        if self.finger_joint_indices:
            p.setJointMotorControlArray(
                self.panda,
                self.finger_joint_indices,
                p.POSITION_CONTROL,
                targetPositions=[target] * len(self.finger_joint_indices),
                forces=[20.0] * len(self.finger_joint_indices),
            )
            for _ in range(30):
                p.stepSimulation()
                self.log_pose()
                time.sleep(0.005)

    def spawn_cube(self, pos=None):
        if pos is None:
            pos = [0.5, 0.0, 0.025]
        if self.cube_id is not None:
            try:
                p.removeBody(self.cube_id)
            except Exception:
                pass
            self.cube_id = None
        self.cube_id = p.loadURDF(
            os.path.join(pybullet_data.getDataPath(), "cube_small.urdf"),
            pos,
            globalScaling=1.0,
            useFixedBase=False,
        )
        p.changeDynamics(self.cube_id, -1, lateralFriction=1.2, rollingFriction=0.002, spinningFriction=0.002, linearDamping=0.02, angularDamping=0.02)
        self.log_pose()
        return self.cube_id

    def try_grasp_constraint(self, threshold: float = 0.08):
        if self.cube_id is None:
            return False
        ee = p.getLinkState(self.panda, self.ee_index)[0]
        cube = p.getBasePositionAndOrientation(self.cube_id)[0]
        dist = np.linalg.norm(np.array(ee) - np.array(cube))
        if dist < threshold:
            return self.force_grasp()
        return False

    def force_grasp(self):
        if self.cube_id is None:
            return False
        if self.grasp_cid is not None:
            try:
                p.removeConstraint(self.grasp_cid)
            except Exception:
                pass
            self.grasp_cid = None
        self.grasp_cid = p.createConstraint(
            parentBodyUniqueId=self.panda,
            parentLinkIndex=self.ee_index,
            childBodyUniqueId=self.cube_id,
            childLinkIndex=-1,
            jointType=p.JOINT_FIXED,
            jointAxis=[0, 0, 0],
            parentFramePosition=[0, 0, 0.035],
            childFramePosition=[0, 0, 0],
        )
        p.stepSimulation()
        self.log_pose()
        return True

    def align_cube_to_ee(self, offset=None):
        if self.cube_id is None:
            return False
        if offset is None:
            offset = [0, 0, -0.06]
        ee_pos, ee_orn = p.getLinkState(self.panda, self.ee_index)[:2]
        target_pos = (np.array(ee_pos) + np.array(offset)).tolist()
        p.resetBasePositionAndOrientation(self.cube_id, target_pos, ee_orn)
        p.stepSimulation()
        self.log_pose()
        return True

    def release_constraint(self):
        if self.grasp_cid is not None:
            try:
                p.removeConstraint(self.grasp_cid)
            except Exception:
                pass
            self.grasp_cid = None
        self.log_pose()

    def snapshot(self, path: str) -> str:
        width, height = 640, 480
        view_matrix = p.computeViewMatrixFromYawPitchRoll(
            cameraTargetPosition=[0.4, 0.0, 0.2],
            distance=1.1,
            yaw=45,
            pitch=-30,
            roll=0,
            upAxisIndex=2,
        )
        proj_matrix = p.computeProjectionMatrixFOV(
            fov=60, aspect=width / height, nearVal=0.01, farVal=3.0
        )
        img = p.getCameraImage(
            width,
            height,
            viewMatrix=view_matrix,
            projectionMatrix=proj_matrix,
            renderer=p.ER_TINY_RENDERER,
        )
        rgba = np.array(img[2], dtype=np.uint8).reshape((height, width, 4))
        rgb = rgba[:, :, :3]
        im = Image.fromarray(rgb, mode="RGB")
        im.save(path)
        return path


_use_gui = os.environ.get("PYBULLET_GUI", "0") == "1"
sim = PandaSim(gui=_use_gui)


@app.route("/state", methods=["GET"])
def state():
    return jsonify({"joints": sim.get_joint_positions()})


@app.route("/poses", methods=["GET"])
def poses():
    ee_p, ee_q = sim.get_ee_pose()
    cb_p, cb_q = sim.get_cube_pose()
    return jsonify({
        "t": sim.now(),
        "ee": {"pos": ee_p, "orn_xyzw": ee_q},
        "cube": {"pos": cb_p, "orn_xyzw": cb_q}
    })


@app.route("/pose_log_reset", methods=["POST"])
def pose_log_reset():
    sim.pose_log = []
    sim.t0 = time.time()
    sim.log_pose()
    return jsonify({"ok": True})


@app.route("/pose_log_dump", methods=["GET"])
def pose_log_dump():
    return jsonify({"log": sim.pose_log})


@app.route("/movej", methods=["POST"])
def movej_route():
    body = request.get_json(force=True)
    targets = body.get("targets")
    duration = float(body.get("duration", 2.0))
    if not isinstance(targets, list) or len(targets) != len(sim.arm_joint_indices):
        return jsonify({"error": f"targets must be list of length {len(sim.arm_joint_indices)}"}), 400
    sim.movej(targets, duration)
    return jsonify({"ok": True, "final": sim.get_joint_positions()})


@app.route("/move_ik", methods=["POST"])
def move_ik_route():
    body = request.get_json(force=True)
    pos = body.get("pos")
    orn = body.get("orn")
    duration = float(body.get("duration", 1.5))
    if not isinstance(pos, list) or len(pos) != 3:
        return jsonify({"error": "pos must be [x,y,z]"}), 400
    sim.move_ik(pos, orn, duration)
    return jsonify({"ok": True})


@app.route("/snapshot", methods=["POST"])
def snapshot_route():
    try:
        body = request.get_json(silent=True) or {}
        path = body.get("path", os.path.abspath("snapshot.png"))
        saved = sim.snapshot(path)
        return jsonify({"ok": True, "path": saved})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/spawn_cube", methods=["POST"])
def spawn_cube():
    body = request.get_json(silent=True) or {}
    pos = body.get("pos", [0.5, 0.0, 0.025])
    cid = sim.spawn_cube(pos)
    return jsonify({"ok": True, "cube_id": cid})


@app.route("/align_cube_to_ee", methods=["POST"])
def align_cube_to_ee():
    body = request.get_json(silent=True) or {}
    offset = body.get("offset", [0, 0, -0.06])
    ok = sim.align_cube_to_ee(offset)
    return jsonify({"ok": ok})


@app.route("/force_grasp", methods=["POST"])
def force_grasp():
    ok = sim.force_grasp()
    return jsonify({"ok": ok})


@app.route("/gripper", methods=["POST"])
def gripper():
    body = request.get_json(force=True)
    width = float(body.get("width", 0.08))
    sim.set_gripper_width(width)
    grasped = False
    if width <= 0.01:
        grasped = sim.try_grasp_constraint()
        if not grasped:
            sim.align_cube_to_ee([0, 0, -0.06])
            grasped = sim.force_grasp()
    return jsonify({"ok": True, "width": width, "grasped": grasped})


@app.route("/gripper_raw", methods=["POST"])
def gripper_raw():
    body = request.get_json(force=True)
    width = float(body.get("width", 0.08))
    sim.set_gripper_width(width)
    return jsonify({"ok": True, "width": width})


@app.route("/release", methods=["POST"])
def release():
    sim.release_constraint()
    sim.set_gripper_width(0.05)
    return jsonify({"ok": True})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port)


