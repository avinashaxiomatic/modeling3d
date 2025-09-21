import os
import csv
import time
import json
import requests
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


BASE = "http://127.0.0.1:5001"


def get(path):
    r = requests.get(f"{BASE}{path}")
    r.raise_for_status()
    return r.json()


def main():
    os.makedirs("analysis", exist_ok=True)
    csv_path = os.path.join("analysis", "poses.csv")

    # reset server-side log and then sample
    requests.post(f"{BASE}/pose_log_reset")
    rows = [("t", "ee_x", "ee_y", "ee_z", "cube_x", "cube_y", "cube_z")]
    # sample at ~10Hz for ~10s
    for _ in range(100):
        d = get("/poses")
        ee = d["ee"]["pos"] if d["ee"]["pos"] is not None else [None, None, None]
        cb = d["cube"]["pos"] if d["cube"]["pos"] is not None else [None, None, None]
        rows.append((d["t"], ee[0], ee[1], ee[2], cb[0], cb[1], cb[2]))
        time.sleep(0.1)

    # write CSV
    with open(csv_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerows(rows)

    # plot z over time (and x/y in subplots)
    ts = [r[0] for r in rows[1:]]
    ee_x = [r[1] for r in rows[1:]]
    ee_y = [r[2] for r in rows[1:]]
    ee_z = [r[3] for r in rows[1:]]
    cb_x = [r[4] for r in rows[1:]]
    cb_y = [r[5] for r in rows[1:]]
    cb_z = [r[6] for r in rows[1:]]

    fig, axs = plt.subplots(3, 1, figsize=(8, 8), constrained_layout=True)
    axs[0].plot(ts, ee_x, label="ee_x")
    axs[0].plot(ts, cb_x, label="cube_x")
    axs[0].set_ylabel("x (m)")
    axs[0].legend()

    axs[1].plot(ts, ee_y, label="ee_y")
    axs[1].plot(ts, cb_y, label="cube_y")
    axs[1].set_ylabel("y (m)")
    axs[1].legend()

    axs[2].plot(ts, ee_z, label="ee_z")
    axs[2].plot(ts, cb_z, label="cube_z")
    axs[2].set_ylabel("z (m)")
    axs[2].set_xlabel("time (s)")
    axs[2].legend()

    # Add GRIP/RELEASE markers for readability (approximate times)
    grip_t = 5.6
    rel_t = 12.0
    for ax in axs:
        ax.axvline(grip_t, color="#2ca02c", linestyle="--", linewidth=1.2, label="GRIP")
        ax.axvline(rel_t, color="#d62728", linestyle="--", linewidth=1.2, label="RELEASE")
        handles, labels = ax.get_legend_handles_labels()
        dedup = dict(zip(labels, handles))
        ax.legend(dedup.values(), dedup.keys())

    png_path = os.path.join("analysis", "poses.png")
    fig.suptitle("End-effector and Cube Poses vs Time")
    fig.savefig(png_path, dpi=150)
    print("wrote", os.path.abspath(csv_path))
    print("wrote", os.path.abspath(png_path))


if __name__ == "__main__":
    main()


