from pathlib import Path
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parents[1] / "FillMeNow" / "Assets.xcassets" / "AppIcon.appiconset" / "AppIcon-1024.png"
OUT.parent.mkdir(parents=True, exist_ok=True)

size = 1024
img = Image.new("RGB", (size, size), (8, 18, 12))
draw = ImageDraw.Draw(img)

# FillMeNow droplet mark.
green = (128, 238, 53)
outer = [
    (512, 115), (390, 315), (315, 470), (290, 590),
    (300, 700), (350, 790), (425, 845), (512, 865),
    (599, 845), (674, 790), (724, 700), (734, 590),
    (709, 470), (634, 315)
]
draw.polygon(outer, fill=green)

inner = [
    (512, 305), (445, 420), (400, 515), (395, 590),
    (410, 660), (450, 710), (512, 728), (574, 710),
    (614, 660), (629, 590), (624, 515), (579, 420)
]
draw.polygon(inner, fill=(8, 18, 12))
draw.ellipse((475, 535, 549, 609), fill=green)

img.save(OUT, "PNG", optimize=True)
print(OUT)
