"""Relative depth for ref.jpg with Depth Anything V2 (small). Writes depth_raw.npy (bigger = nearer) and depth.png.
Needs: pip install torch transformers pillow numpy   (CPU torch is fine; ~1 minute)."""
import numpy as np, torch
from PIL import Image
from transformers import AutoImageProcessor, AutoModelForDepthEstimation
name = "depth-anything/Depth-Anything-V2-Small-hf"
proc = AutoImageProcessor.from_pretrained(name); model = AutoModelForDepthEstimation.from_pretrained(name).eval()
im = Image.open("ref.jpg").convert("RGB")
with torch.no_grad(): out = model(**proc(images=im, return_tensors="pt")).predicted_depth
d = torch.nn.functional.interpolate(out[None], size=im.size[::-1], mode="bicubic")[0, 0].numpy()
np.save("depth_raw.npy", d); Image.fromarray((255 * (d - d.min()) / (d.max() - d.min())).astype("uint8")).save("depth.png"); print("depth", d.shape)
