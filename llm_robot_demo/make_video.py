import os
import imageio.v2 as imageio
import glob


def main():
    frames = []
    # Prefer frames from frames/ if present, otherwise fall back to snapshots
    frame_files = sorted(glob.glob("frames/frame_*.png"))
    if not frame_files:
        frame_files = [fn for fn in ["snapshot_1.png", "snapshot_2.png", "snapshot_3.png"] if os.path.exists(fn)]
    for fn in frame_files:
        frames.append(imageio.imread(fn))
    if not frames:
        print("No frames found.")
        return
    # If using frames/, target ~30 fps
    fps = 30 if frame_files and frame_files[0].startswith("frames/") else 2
    out = "demo.mp4"
    imageio.mimsave(out, frames, fps=fps, codec="libx264")
    print("wrote", os.path.abspath(out))


if __name__ == "__main__":
    main()


