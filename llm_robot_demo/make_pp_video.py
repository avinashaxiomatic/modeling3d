import os
import glob
import imageio.v2 as imageio


def main():
    frames = sorted(glob.glob(os.path.join("frames", "pp_*.png")))
    if not frames:
        print("No pick-and-place frames found under frames/pp_*.png")
        return
    imgs = [imageio.imread(fn) for fn in frames]
    out = "pick_place.mp4"
    imageio.mimsave(out, imgs, fps=5, codec="libx264")
    print("wrote", os.path.abspath(out))


if __name__ == "__main__":
    main()


