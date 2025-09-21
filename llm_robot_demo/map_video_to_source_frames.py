import os
import csv
import glob


def main():
    project_root = os.path.dirname(os.path.abspath(__file__))
    src_dir = os.path.join(project_root, "frames")
    vid_dir = os.path.join(project_root, "video_frames")
    out_csv = os.path.join(vid_dir, "video_frame_map.csv")

    src_frames = sorted(glob.glob(os.path.join(src_dir, "pp_*.png")))
    vid_frames = sorted(glob.glob(os.path.join(vid_dir, "frame_*.png")))

    if not src_frames or not vid_frames:
        raise SystemExit("No frames found to map. Ensure frames/ and video_frames/ exist.")

    # FPS used in captioned MP4 encoder
    fps = 8.0
    L = min(len(src_frames), len(vid_frames))

    with open(out_csv, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "video_index_1based",
            "video_frame",
            "video_time_sec",
            "source_index_1based",
            "source_frame",
            "event",
        ])
        for i in range(L):
            v_idx = i + 1
            s_idx = i + 1
            v_path = os.path.relpath(vid_frames[i], project_root)
            s_path = os.path.relpath(src_frames[i], project_root)
            t_sec = (v_idx - 1) / fps
            name = os.path.basename(s_path)
            event = "grip" if "_grip_" in name else ("release" if "_release_" in name else "")
            w.writerow([v_idx, v_path, f"{t_sec:.3f}", s_idx, s_path, event])

    print("wrote", out_csv)
    print("mapped_pairs", L)


if __name__ == "__main__":
    main()


