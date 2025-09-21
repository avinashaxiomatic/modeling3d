import os
import glob
import imageio.v2 as imageio
from PIL import Image, ImageDraw, ImageFont
import numpy as np


def overlay_text(img, text: str, position: str = "bottom"):
    if not isinstance(img, Image.Image):
        img = Image.fromarray(img)
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.load_default()
    except Exception:
        font = None
    W, H = img.size
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]

    if position == "bottom":
        x = (W - tw) // 2
        y = H - th - 20
        bg_color = (0, 0, 0)
    elif position == "topleft":
        x = 14
        y = 14
        bg_color = (180, 0, 0)
    else:
        x = 10
        y = 10
        bg_color = (0, 0, 0)

    pad = 8
    rect = [x - pad, y - pad, x + tw + pad, y + th + pad]
    draw.rectangle(rect, fill=bg_color)
    draw.text((x, y), text, fill=(255, 255, 255), font=font)
    return img


def main():
    frames = sorted(glob.glob(os.path.join("frames", "pp_*.png")))
    if not frames:
        print("No pick-and-place frames found under frames/pp_*.png")
        return

    base_caption = "LLM: pick the cube, move right, place, home"

    imgs = []
    for fn in frames:
        img = Image.open(fn).convert("RGB")
        img = overlay_text(img, base_caption, position="bottom")
        name = os.path.basename(fn)
        if "_grip_" in name:
            img = overlay_text(img, "GRIP", position="topleft")
        if "_release_" in name:
            img = overlay_text(img, "RELEASE", position="topleft")
        imgs.append(np.array(img))

    out = "pick_place_captioned.mp4"
    imageio.mimsave(out, imgs, fps=8, codec="libx264")
    print("wrote", os.path.abspath(out))


if __name__ == "__main__":
    main()


