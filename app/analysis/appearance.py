import cv2
import numpy as np

from app.config import TEXTURE_PROFILES


def crop_from_box(frame, x1, y1, x2, y2):
    h, w = frame.shape[:2]

    x1 = max(0, min(x1, w - 1))
    x2 = max(0, min(x2, w))
    y1 = max(0, min(y1, h - 1))
    y2 = max(0, min(y2, h))

    if x2 <= x1 or y2 <= y1:
        return None

    return frame[y1:y2, x1:x2].copy()


def extract_dominant_color(crop):
    """
    Extrait une couleur dominante approximative depuis la zone détectée.
    On privilégie les tons proches du bois si possible.
    Retour : tuple BGR
    """
    if crop is None or crop.size == 0:
        return None

    small = cv2.resize(crop, (120, 120), interpolation=cv2.INTER_AREA)
    hsv = cv2.cvtColor(small, cv2.COLOR_BGR2HSV)

    # Masque approximatif pour tons bois / marron / beige
    lower1 = np.array([5, 30, 20], dtype=np.uint8)
    upper1 = np.array([35, 255, 255], dtype=np.uint8)

    lower2 = np.array([0, 20, 20], dtype=np.uint8)
    upper2 = np.array([15, 255, 255], dtype=np.uint8)

    mask1 = cv2.inRange(hsv, lower1, upper1)
    mask2 = cv2.inRange(hsv, lower2, upper2)
    mask = cv2.bitwise_or(mask1, mask2)

    pixels = small[mask > 0]

    if len(pixels) < 200:
        pixels = small.reshape(-1, 3)

    dominant = np.median(pixels, axis=0)
    return tuple(int(v) for v in dominant)


def bgr_to_hsv_single(bgr):
    arr = np.uint8([[bgr]])
    hsv = cv2.cvtColor(arr, cv2.COLOR_BGR2HSV)[0][0]
    return tuple(int(v) for v in hsv)


def classify_wood_tone(bgr_color):
    """
    Classe grossièrement la teinte observée.
    """
    if bgr_color is None:
        return "classic_brown"

    h, s, v = bgr_to_hsv_single(bgr_color)

    if v < 70:
        return "dark_brown"

    if h < 12 and s > 90:
        return "reddish_brown"

    if v > 145 and s < 140:
        return "light_brown"

    return "classic_brown"


def choose_texture_profile(wood_tone):
    """
    Retourne un dictionnaire avec la texture choisie.
    """
    path = TEXTURE_PROFILES.get(wood_tone, TEXTURE_PROFILES["classic_brown"])

    return {
        "tone": wood_tone,
        "name": path.name,
        "path": str(path),
        "exists": path.exists(),
    }