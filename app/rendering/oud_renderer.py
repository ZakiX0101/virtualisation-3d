import os
import sys
import cv2
import numpy as np
import textwrap
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

from app.data.oud_parts import OUD_PARTS
from app.config import BLENDER_FILE, OUD_WINDOW_TITLE


def load_font(size=22):
    font_candidates = [
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/Library/Fonts/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
    ]

    for path in font_candidates:
        try:
            return ImageFont.truetype(path, size=size)
        except Exception:
            continue

    return ImageFont.load_default()


TITLE_FONT = load_font(28)
TEXT_FONT = load_font(18)
SMALL_FONT = load_font(15)


def safe_texture_preview(texture_path, fallback_bgr=(90, 120, 160), size=(180, 110)):
    w, h = size
    texture = None

    if texture_path and Path(texture_path).exists():
        texture = cv2.imread(str(texture_path))

    if texture is None:
        texture = np.full((h, w, 3), fallback_bgr, dtype=np.uint8)
        for i in range(0, w, 16):
            cv2.line(texture, (i, 0), (i, h), (fallback_bgr[0] - 10, fallback_bgr[1] - 10, fallback_bgr[2] - 10), 1)
    else:
        texture = cv2.resize(texture, (w, h))

    return texture


def create_oud_composition_view(wood_tone, texture_profile, dominant_color=None):
    """
    Vue pédagogique du oud.
    Ce n'est pas encore un vrai rendu 3D temps réel :
    c'est une vue de composition stylisée et exploitable immédiatement.
    """
    canvas = np.full((650, 1100, 3), (22, 24, 30), dtype=np.uint8)

    # Couleur du bois utilisée pour le schéma
    if dominant_color is None:
        dominant_color = (70, 100, 140)

    body_color = dominant_color
    outline = (230, 230, 230)
    accent = (0, 255, 180)

    # ---- Dessin du oud stylisé ----
    # Caisse
    body_center = (260, 380)
    axes = (135, 205)
    cv2.ellipse(canvas, body_center, axes, 0, 0, 360, body_color, -1)
    cv2.ellipse(canvas, body_center, axes, 0, 0, 360, outline, 2)

    # Table (plus claire)
    table_color = tuple(min(c + 25, 255) for c in body_color)
    cv2.ellipse(canvas, body_center, (118, 188), 0, 0, 360, table_color, -1)
    cv2.ellipse(canvas, body_center, (118, 188), 0, 0, 360, outline, 1)

    # Rosace
    cv2.circle(canvas, (235, 345), 24, (40, 40, 40), 2)
    cv2.circle(canvas, (235, 345), 14, (40, 40, 40), 2)

    # Chevalet
    cv2.rectangle(canvas, (205, 475), (295, 490), (35, 35, 35), -1)
    cv2.rectangle(canvas, (205, 475), (295, 490), outline, 1)

    # Manche
    cv2.rectangle(canvas, (315, 235), (505, 275), body_color, -1)
    cv2.rectangle(canvas, (315, 235), (505, 275), outline, 2)

    # Boite a chevilles
    pegbox_pts = np.array([
        [505, 230],
        [585, 205],
        [605, 222],
        [527, 285],
        [505, 275]
    ], dtype=np.int32)
    cv2.fillPoly(canvas, [pegbox_pts], body_color)
    cv2.polylines(canvas, [pegbox_pts], True, outline, 2)

    # Chevilles
    peg_positions = [(550, 220), (565, 230), (580, 240), (560, 255), (545, 266), (528, 275)]
    for x, y in peg_positions:
        cv2.circle(canvas, (x, y), 5, (20, 20, 20), -1)
        cv2.circle(canvas, (x, y), 5, outline, 1)

    # Cordes
    for offset in [-18, -10, -2, 6, 14, 22]:
        x_start = 220 + offset
        x_end = 555 + int(offset * 0.6)
        cv2.line(canvas, (x_start, 480), (x_end, 238), (235, 235, 235), 1)

    # Lignes d'annotation
    annotation_color = accent
    points = {
        "Caisse": ((145, 380), (660, 165)),
        "Table": ((368, 380), (660, 210)),
        "Rosace": ((235, 345), (660, 255)),
        "Chevalet": ((295, 482), (660, 300)),
        "Manche": ((450, 255), (660, 345)),
        "Boite a chevilles": ((585, 220), (660, 390)),
        "Chevilles": ((560, 245), (660, 435)),
        "Cordes": ((420, 320), (660, 480)),
    }

    for name, (src, dst) in points.items():
        cv2.line(canvas, src, dst, annotation_color, 1)
        cv2.circle(canvas, src, 4, annotation_color, -1)

    # ---- Zone texte avec Pillow ----
    pil_img = Image.fromarray(cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(pil_img)

    draw.text((30, 22), "Composition du OUD detecte", font=TITLE_FONT, fill=(0, 255, 180))
    draw.text((32, 62), f"Teinte analysee : {wood_tone}", font=TEXT_FONT, fill=(245, 245, 245))
    draw.text((32, 88), f"Texture associee : {texture_profile.get('name', 'inconnue')}", font=TEXT_FONT, fill=(245, 245, 245))
    draw.text((32, 114), "Cette vue peut etre remplacee plus tard par un vrai modele 3D GLB/Blender.",
              font=SMALL_FONT, fill=(180, 180, 180))

    y = 152
    for part in OUD_PARTS:
        draw.text((690, y), f"{part['name']}", font=TEXT_FONT, fill=(0, 255, 180))
        wrapped = textwrap.wrap(part["role"], width=42)
        yy = y + 22
        for line in wrapped:
            draw.text((690, yy), line, font=SMALL_FONT, fill=(235, 235, 235))
            yy += 18
        y = yy + 10

    canvas = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

    # Aperçu texture
    texture_preview = safe_texture_preview(
        texture_profile.get("path"),
        fallback_bgr=dominant_color if dominant_color is not None else (90, 120, 160),
        size=(220, 120)
    )
    canvas[24:144, 840:1060] = texture_preview
    cv2.rectangle(canvas, (840, 24), (1060, 144), (255, 255, 255), 1)
    cv2.putText(canvas, "Texture preview", (845, 162), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (230, 230, 230), 1, cv2.LINE_AA)

    return canvas


def show_oud_composition_view(wood_tone, texture_profile, dominant_color=None):
    canvas = create_oud_composition_view(wood_tone, texture_profile, dominant_color)
    cv2.imshow(OUD_WINDOW_TITLE, canvas)


def close_oud_window():
    try:
        cv2.destroyWindow(OUD_WINDOW_TITLE)
    except Exception:
        pass


def try_open_blender_file():
    """
    Ouvre le fichier Blender si possible.
    """
    if not BLENDER_FILE.exists():
        print(f"[INFO] Fichier Blender introuvable : {BLENDER_FILE}")
        return

    try:
        if sys.platform.startswith("win"):
            os.startfile(str(BLENDER_FILE))
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(BLENDER_FILE)])
        else:
            subprocess.Popen(["xdg-open", str(BLENDER_FILE)])
        print(f"[INFO] Ouverture de Blender : {BLENDER_FILE}")
    except Exception as e:
        print(f"[ERREUR] Impossible d'ouvrir le fichier Blender : {e}")