import cv2

from app.ar.panel import draw_label_tag, draw_history_panel, draw_oud_status_panel


def draw_detection_overlay(frame, label, info_text, box, wood_tone=None, texture_name=None, dominant_color=None):
    x1, y1, x2, y2 = box

    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 180), 2)
    frame = draw_label_tag(frame, label, x1, y1)
    frame = draw_history_panel(frame, label, info_text, x1, y1, x2, y2)

    if label == "oud" and wood_tone and texture_name:
        frame = draw_oud_status_panel(frame, wood_tone, texture_name, dominant_color)

    return frame