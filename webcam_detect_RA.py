import cv2
import numpy as np
import textwrap
from ultralytics import YOLO
from PIL import Image, ImageDraw, ImageFont

# =========================
# Informations historiques
INSTRUMENT_INFO = {
    "bendir": (
        "Le bendir est un instrument de percussion traditionnel d’Afrique du Nord. "
        "Constitué d’un cadre en bois et d’une peau tendue, il possède souvent des "
        "cordes de timbre qui lui donnent un son bourdonnant. Il est très présent "
        "dans les musiques amazighes et soufies."
    ),
    "guembri": (
        "Le guembri est un luth traditionnel à trois cordes, emblématique de la "
        "musique spirituelle gnawa. Sa caisse de résonance est taillée dans un tronc "
        "d’arbre creusé et recouverte de peau de chameau."
    ),
    "oud": (
        "Le oud est l’un des instruments majeurs de la musique arabe et orientale. "
        "C’est un luth à manche court sans frettes, reconnaissable à sa grande caisse "
        "de résonance en forme de demi-poire, permettant des mélodies très riches."
    ),
    "loutar": (
        "Le loutar est un luth rustique traditionnel marocain, profondément ancré "
        "dans la culture amazighe, notamment dans le Moyen Atlas. Il possède une "
        "caisse circulaire recouverte de peau et produit un son très percussif."
    ),
}

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

TITLE_FONT = load_font(24)
TEXT_FONT = load_font(19)
TAG_FONT = load_font(20)


def normalize_label(label: str) -> str:
    """
    Normalise le nom de classe renvoyé par YOLO.
    Si le modèle renvoie 'outar', on le remplace par 'loutar'.
    """
    label = label.lower().strip()

    if label == "outar":
        return "loutar"

    return label

def draw_rounded_rectangle(draw, box, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)

def draw_text_with_pillow(img, text, position, font, fill):
    """
    Dessine un texte Unicode sur une image OpenCV via Pillow.
    """
    pil_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(pil_img)
    draw.text(position, text, font=font, fill=fill)
    return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

def draw_label_tag(img, label, x1, y1):
    """
    Petit cartouche avec le nom de l’instrument.
    """
    h, w = img.shape[:2]

    pil_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)).convert("RGBA")
    overlay = Image.new("RGBA", pil_img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    title = label.upper()
    text_bbox = draw.textbbox((0, 0), title, font=TAG_FONT)
    text_w = text_bbox[2] - text_bbox[0]
    text_h = text_bbox[3] - text_bbox[1]

    padding_x = 14
    padding_y = 8

    box_w = text_w + 2 * padding_x
    box_h = text_h + 2 * padding_y

    tag_x1 = x1
    tag_y1 = max(y1 - box_h - 8, 8)
    tag_x2 = min(tag_x1 + box_w, w - 8)
    tag_y2 = tag_y1 + box_h

    if tag_x2 - tag_x1 < box_w:
        tag_x1 = max(w - box_w - 8, 8)
        tag_x2 = tag_x1 + box_w

    draw_rounded_rectangle(
        draw,
        [tag_x1, tag_y1, tag_x2, tag_y2],
        radius=12,
        fill=(15, 18, 24, 220),
        outline=(0, 255, 180, 230),
        width=2
    )

    text_x = tag_x1 + padding_x
    text_y = tag_y1 + padding_y - 1

    draw.text((text_x, text_y), title, font=TAG_FONT, fill=(0, 255, 180, 255))

    combined = Image.alpha_composite(pil_img, overlay)
    return cv2.cvtColor(np.array(combined.convert("RGB")), cv2.COLOR_RGB2BGR)

def draw_ar_panel(img, label, x1, y1, x2, y2):
    """
    Dessine un panneau AR esthétique avec :
    - accents corrects
    - fond semi-transparent
    - titre propre
    - texte multilignes bien formaté
    - ligne de liaison avec l’objet détecté
    """
    h, w = img.shape[:2]
    info_text = INSTRUMENT_INFO.get(label, "Description non disponible.")
    title = label.upper()

    pil_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)).convert("RGBA")
    overlay = Image.new("RGBA", pil_img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Paramètres du panneau
    panel_width = 440
    padding_x = 18
    padding_y = 14
    radius = 18
    title_gap = 12
    line_gap = 7

    # Wrap du texte
    wrapped_lines = textwrap.wrap(info_text, width=42)

    # Mesures
    title_bbox = draw.textbbox((0, 0), title, font=TITLE_FONT)
    title_h = title_bbox[3] - title_bbox[1]

    line_heights = []
    for line in wrapped_lines:
        bbox = draw.textbbox((0, 0), line, font=TEXT_FONT)
        line_heights.append(bbox[3] - bbox[1])

    text_block_h = sum(line_heights) + max(0, len(line_heights) - 1) * line_gap
    panel_height = padding_y * 2 + title_h + title_gap + text_block_h

    # Positionnement automatique
    panel_x = x1
    panel_y = y1 - panel_height - 20

    if panel_x + panel_width > w - 8:
        panel_x = max(w - panel_width - 8, 8)

    if panel_y < 8:
        panel_y = min(y2 + 20, h - panel_height - 8)

    # Couleurs
    panel_fill = (15, 18, 24, 215)
    border_color = (0, 255, 180, 235)
    title_color = (0, 255, 180, 255)
    text_color = (245, 245, 245, 255)
    accent_color = (0, 255, 180, 140)

    # Fond du panneau
    draw_rounded_rectangle(
        draw,
        [panel_x, panel_y, panel_x + panel_width, panel_y + panel_height],
        radius=radius,
        fill=panel_fill,
        outline=border_color,
        width=2
    )

    # Barre décorative
    draw.rounded_rectangle(
        [panel_x + 8, panel_y + 8, panel_x + 12, panel_y + panel_height - 8],
        radius=4,
        fill=accent_color
    )

    # Titre
    text_x = panel_x + padding_x + 8
    text_y = panel_y + padding_y
    draw.text((text_x, text_y), title, font=TITLE_FONT, fill=title_color)

    # Séparateur
    sep_y = text_y + title_h + 6
    draw.line(
        [(text_x, sep_y), (panel_x + panel_width - padding_x, sep_y)],
        fill=(80, 220, 180, 170),
        width=1
    )

    # Corps du texte
    current_y = sep_y + 10
    for line in wrapped_lines:
        draw.text((text_x, current_y), line, font=TEXT_FONT, fill=text_color)
        bbox = draw.textbbox((0, 0), line, font=TEXT_FONT)
        line_h = bbox[3] - bbox[1]
        current_y += line_h + line_gap

    # Ligne de liaison entre l'objet et le panneau
    object_anchor = ((x1 + x2) // 2, y1 if panel_y < y1 else y2)
    panel_anchor_x = panel_x + 30
    panel_anchor_y = panel_y + panel_height if panel_y < y1 else panel_y

    draw.line(
        [object_anchor, (panel_anchor_x, panel_anchor_y)],
        fill=(0, 255, 180, 220),
        width=2
    )

    # Petit point sur l'objet
    r = 5
    draw.ellipse(
        [
            object_anchor[0] - r,
            object_anchor[1] - r,
            object_anchor[0] + r,
            object_anchor[1] + r
        ],
        fill=(0, 255, 180, 255)
    )

    combined = Image.alpha_composite(pil_img, overlay)
    return cv2.cvtColor(np.array(combined.convert("RGB")), cv2.COLOR_RGB2BGR)

# =========================
# Chargement du modèle YOLO
# =========================
model = YOLO("runs/detect/train/weights/best.pt")

# =========================
# Ouverture caméra
# =========================
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Erreur : impossible d’ouvrir la caméra.")
    raise SystemExit

# =========================
# Boucle principale
# =========================
while True:
    ret, frame = cap.read()
    if not ret:
        print("Erreur : impossible de lire l’image caméra.")
        break

    results = model(frame, conf=0.75, verbose=False)[0]

    for box in results.boxes:
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        cls = int(box.cls[0])

        raw_label = model.names[cls]
        label = normalize_label(raw_label)

        # Cadre autour de l’objet
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 180), 2)

        # Petit cartouche du nom
        frame = draw_label_tag(frame, label, x1, y1)

        # Panneau d’information AR
        frame = draw_ar_panel(frame, label, x1, y1, x2, y2)

    cv2.imshow("Smart Heritage AR - Detection", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

# =========================
# Libération ressources
# =========================
cap.release()
cv2.destroyAllWindows()