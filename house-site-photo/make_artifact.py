"""Inline frames + libs into one self-contained HTML (needed for hosting where relative files are awkward). usage: python3 make_artifact.py OUT.html"""
import base64, glob, re, sys
s = open("index.html").read()
vend = "".join(open(f"vendor/{f}").read() + "\n" for f in ("gsap.min.js", "ScrollTrigger.min.js", "lenis.min.js"))
assert "</script" not in vend
frames = ["data:image/webp;base64," + base64.b64encode(open(f, "rb").read()).decode() for f in sorted(glob.glob("frames/f_*.webp"))]
s = re.sub(r'<script src="vendor/[^"]+"></script>', "", s)
s = s.replace("<script>\nconst reduce", "<script>" + vend + "</script>\n<script>window.FRAMES=" + str(frames).replace("'", '"') + ";\nconst reduce", 1)
head, body = s.split("</head>")[0], s.split("<body>")[1].rsplit("</body>", 1)[0]
open(sys.argv[1], "w").write(re.search(r"<title>.*?</title>", head).group(0) + "\n" + re.search(r"<style>.*?</style>", head, re.S).group(0) + "\n" + body)
