"""ref_blend.png = 60% AI upscale + 40% plain bicubic. The AI part alone looks painted and etches foliage; the blend keeps photographic grain."""
import cv2
ref = cv2.imread("ref.jpg"); sr = cv2.imread("ref_sr4.png")
bic = cv2.resize(ref, (sr.shape[1], sr.shape[0]), interpolation=cv2.INTER_CUBIC)
cv2.imwrite("ref_blend.png", cv2.addWeighted(sr, 0.6, bic, 0.4, 0)); print("ref_blend.png")
