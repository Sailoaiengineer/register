"""4x AI upscale (Swin2SR, trained for JPEG-compressed images), tiled with overlap so it fits in CPU memory."""
import numpy as np, torch
from PIL import Image
from transformers import AutoImageProcessor, Swin2SRForImageSuperResolution
name = "caidas/swin2SR-compressed-sr-x4-48"
proc = AutoImageProcessor.from_pretrained(name); model = Swin2SRForImageSuperResolution.from_pretrained(name).eval()
im = Image.open("ref.jpg").convert("RGB"); W, H = im.size; S = 4; T, O = 160, 16
src = np.asarray(im, np.float32) / 255; out = np.zeros((H * S, W * S, 3), np.float32); wsum = np.zeros((H * S, W * S, 1), np.float32)
torch.set_num_threads(4)
for y in range(0, H, T - 2 * O):
    for x in range(0, W, T - 2 * O):
        y0, x0 = min(y, max(H - T, 0)), min(x, max(W - T, 0)); tile = src[y0:y0 + T, x0:x0 + T]
        t = torch.from_numpy(tile.transpose(2, 0, 1))[None]
        with torch.no_grad(): r = model(pixel_values=t).reconstruction[0].clamp(0, 1).numpy().transpose(1, 2, 0)
        h, w = r.shape[:2]; wy = np.minimum(np.arange(h) + 1, h - np.arange(h))[:, None]; wx = np.minimum(np.arange(w) + 1, w - np.arange(w))[None, :]
        wt = np.minimum(np.minimum(wy, wx), O * S)[..., None].astype(np.float32)   # feathered blend across tile seams
        out[y0 * S:y0 * S + h, x0 * S:x0 * S + w] += r * wt; wsum[y0 * S:y0 * S + h, x0 * S:x0 * S + w] += wt
        print(y0, x0, flush=True)
Image.fromarray((out / np.maximum(wsum, 1e-6) * 255).clip(0, 255).astype(np.uint8)).save("ref_sr4.png"); print("done", out.shape)
