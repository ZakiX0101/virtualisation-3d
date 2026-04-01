import cv2
import numpy as np
import textwrap
from PIL import Image, ImageDraw, ImageFont


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
SMALL_FONT = load_font(16)


def draw_rounded_rectangle(draw, box, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def to_pil_rgba(img_bgr):
    return Image.fromarray(cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)).convert("RGBA")


def from_pil_rgba(pil_img):
    return cv2.cvtColor(np.array(pil_img.convert("RGB")), cv2.COLOR_RGB2BGR)


def draw_label_tag(img, label, x1, y1):
    h, w = img.shape[:2]

    pil_img = to_pil_rgba(img)
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
    return from_pil_rgba(combined)


def draw_history_panel(img, label, info_text, x1, y1, x2, y2):
    h, w = img.shape[:2]

    pil_img = to_pil_rgba(img)
    overlay = Image.new("RGBA", pil_img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    title = f"{label.upper()} - Historique"
    wrapped_lines = textwrap.wrap(info_text, width=42)

    panel_width = 460
    padding_x = 18
    padding_y = 14
    radius = 18
    title_gap = 12
    line_gap = 7

    title_bbox = draw.textbbox((0, 0), title, font=TITLE_FONT)
    title_h = title_bbox[3] - title_bbox[1]

    line_heights = []
    for line in wrapped_lines:
        bbox = draw.textbbox((0, 0), line, font=TEXT_FONT)
        line_heights.append(bbox[3] - bbox[1])

    text_block_h = sum(line_heights) + max(0, len(line_heights) - 1) * line_gap
    panel_height = padding_y * 2 + title_h + title_gap + text_block_h

    panel_x = x1
    panel_y = y1 - panel_height - 20

    if panel_x + panel_width > w - 8:
        panel_x = max(w - panel_width - 8, 8)

    if panel_y < 8:
        panel_y = min(y2 + 20, h - panel_height - 8)

    panel_fill = (15, 18, 24, 215)
    border_color = (0, 255, 180, 235)
    title_color = (0, 255, 180, 255)
    text_color = (245, 245, 245, 255)
    accent_color = (0, 255, 180, 140)

    draw_rounded_rectangle(
        draw,
        [panel_x, panel_y, panel_x + panel_width, panel_y + panel_height],
        radius=radius,
        fill=panel_fill,
        outline=border_color,
        width=2
    )

    draw.rounded_rectangle(
        [panel_x + 8, panel_y + 8, panel_x + 12, panel_y + panel_height - 8],
        radius=4,
        fill=accent_color
    )

    text_x = panel_x + padding_x + 8
    text_y = panel_y + padding_y
    draw.text((text_x, text_y), title, font=TITLE_FONT, fill=title_color)

    sep_y = text_y + title_h + 6
    draw.line(
        [(text_x, sep_y), (panel_x + panel_width - padding_x, sep_y)],
        fill=(80, 220, 180, 170),
        width=1
    )

    current_y = sep_y + 10
    for line in wrapped_lines:
        draw.text((text_x, current_y), line, font=TEXT_FONT, fill=text_color)
        bbox = draw.textbbox((0, 0), line, font=TEXT_FONT)
        line_h = bbox[3] - bbox[1]
        current_y += line_h + line_gap

    object_anchor = ((x1 + x2) // 2, y1 if panel_y < y1 else y2)
    panel_anchor_x = panel_x + 30
    panel_anchor_y = panel_y + panel_height if panel_y < y1 else panel_y

    draw.line(
        [object_anchor, (panel_anchor_x, panel_anchor_y)],
        fill=(0, 255, 180, 220),
        width=2
    )

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
    return from_pil_rgba(combined)


def draw_oud_status_panel(img, wood_tone, texture_name, dominant_color=None):
    h, w = img.shape[:2]

    pil_img = to_pil_rgba(img)
    overlay = Image.new("RGBA", pil_img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    panel_w = 360
    panel_h = 108
    x1 = 14
    y1 = h - panel_h - 14
    x2 = x1 + panel_w
    y2 = y1 + panel_h

    draw_rounded_rectangle(
        draw,
        [x1, y1, x2, y2],
        radius=16,
        fill=(10, 14, 20, 210),
        outline=(0, 255, 180, 220),
        width=2
    )

    draw.text((x1 + 16, y1 + 12), "Analyse visuelle du OUD", font=TITLE_FONT, fill=(0, 255, 180, 255))
    draw.text((x1 + 16, y1 + 48), f"Teinte detectee : {wood_tone}", font=TEXT_FONT, fill=(245, 245, 245, 255))
    draw.text((x1 + 16, y1 + 75), f"Texture choisie : {texture_name}", font=TEXT_FONT, fill=(245, 245, 245, 255))

    if dominant_color is not None:
        b, g, r = dominant_color
        color_box = [x2 - 78, y1 + 22, x2 - 24, y1 + 76]
        draw_rounded_rectangle(
            draw,
            color_box,
            radius=10,
            fill=(r, g, b, 255),
            outline=(255, 255, 255, 220),
            width=2
        )

    combined = Image.alpha_composite(pil_img, overlay)
    return from_pil_rgba(combined)