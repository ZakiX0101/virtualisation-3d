import cv2
import numpy as np
from functools import lru_cache

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


def center_crop(img, ratio=0.72):
    """
    Garde seulement la zone centrale pour réduire l'influence du fond.
    """
    if img is None or img.size == 0:
        return None

    h, w = img.shape[:2]
    new_w = max(10, int(w * ratio))
    new_h = max(10, int(h * ratio))

    x1 = (w - new_w) // 2
    y1 = (h - new_h) // 2
    x2 = x1 + new_w
    y2 = y1 + new_h

    return img[y1:y2, x1:x2].copy()


def build_wood_mask(img_bgr):
    """
    Masque plus robuste pour isoler les tons bois
    et exclure le blanc du fond + le noir des cordes.
    """
    if img_bgr is None or img_bgr.size == 0:
        return None

    hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)

    # Bois beige -> brun -> brun rouge
    lower = np.array([4, 18, 35], dtype=np.uint8)
    upper = np.array([32, 255, 245], dtype=np.uint8)

    mask = cv2.inRange(hsv, lower, upper)

    # Retirer les zones trop sombres (cordes) et trop claires (fond blanc)
    h_chan, s_chan, v_chan = cv2.split(hsv)
    dark_mask = cv2.inRange(v_chan, 0, 40)
    bright_mask = cv2.inRange(v_chan, 246, 255)

    mask = cv2.bitwise_and(mask, cv2.bitwise_not(dark_mask))
    mask = cv2.bitwise_and(mask, cv2.bitwise_not(bright_mask))

    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.medianBlur(mask, 5)

    return mask


def masked_pixels(img, mask):
    pixels = img[mask > 0]
    if len(pixels) < 80:
        pixels = img.reshape(-1, img.shape[-1])
    return pixels


def masked_median_bgr(img_bgr, mask):
    pixels = masked_pixels(img_bgr, mask)
    med = np.median(pixels, axis=0)
    return tuple(int(v) for v in med)


def masked_mean_lab(img_bgr, mask):
    lab = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2LAB)
    pixels = masked_pixels(lab, mask)
    mean = np.mean(pixels, axis=0)
    return tuple(float(v) for v in mean)


def masked_mean_hsv(img_bgr, mask):
    hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
    pixels = masked_pixels(hsv, mask)
    mean = np.mean(pixels, axis=0)
    return tuple(float(v) for v in mean)


def compute_edge_density(img_bgr, mask):
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 70, 140)

    valid = (mask > 0)
    total = np.count_nonzero(valid)

    if total == 0:
        total = gray.size
        edge_pixels = np.count_nonzero(edges)
    else:
        edge_pixels = np.count_nonzero(edges[valid])

    return float(edge_pixels) / float(total)


def extract_appearance_features(img_bgr):
    """
    Extrait des caractéristiques plus discriminantes.
    """
    if img_bgr is None or img_bgr.size == 0:
        return None

    work = center_crop(img_bgr, ratio=0.72)
    work = cv2.resize(work, (180, 180), interpolation=cv2.INTER_AREA)

    mask = build_wood_mask(work)
    if mask is None:
        return None

    median_bgr = masked_median_bgr(work, mask)
    mean_lab = masked_mean_lab(work, mask)
    mean_hsv = masked_mean_hsv(work, mask)
    edge_density = compute_edge_density(work, mask)

    return {
        "median_bgr": median_bgr,
        "mean_lab": mean_lab,
        "mean_hsv": mean_hsv,
        "edge_density": edge_density,
    }


@lru_cache(maxsize=32)
def extract_texture_features(texture_path_str):
    img = cv2.imread(texture_path_str)
    if img is None:
        return None
    return extract_appearance_features(img)


def texture_distance(obs, ref):
    """
    Distance plus stable entre le crop capturé et une texture.
    On privilégie surtout la couleur.
    """
    obs_lab = np.array(obs["mean_lab"], dtype=np.float32)
    ref_lab = np.array(ref["mean_lab"], dtype=np.float32)

    obs_hsv = np.array(obs["mean_hsv"], dtype=np.float32)
    ref_hsv = np.array(ref["mean_hsv"], dtype=np.float32)

    color_dist_lab = np.linalg.norm(obs_lab - ref_lab)
    color_dist_hsv = np.linalg.norm(obs_hsv - ref_hsv) * 0.35
    edge_dist = abs(obs["edge_density"] - ref["edge_density"]) * 20.0

    return float(color_dist_lab + color_dist_hsv + edge_dist)


def choose_best_texture_from_crop(crop):
    """
    Compare le crop du oud aux 6 textures et choisit la meilleure.
    """
    obs = extract_appearance_features(crop)

    if obs is None:
        fallback_key = "wood_classic"
        fallback_path = TEXTURE_PROFILES[fallback_key]
        return {
            "tone": fallback_key,
            "name": fallback_path.name,
            "path": str(fallback_path),
            "exists": fallback_path.exists(),
            "score": None,
            "dominant_bgr": (140, 110, 80),
            "ranking": [],
        }

    candidates = []

    for texture_key, texture_path in TEXTURE_PROFILES.items():
        if not texture_path.exists():
            continue

        ref = extract_texture_features(str(texture_path))
        if ref is None:
            continue

        score = texture_distance(obs, ref)
        candidates.append({
            "key": texture_key,
            "name": texture_path.name,
            "path": str(texture_path),
            "score": round(score, 2),
        })

    if not candidates:
        fallback_key = "wood_classic"
        fallback_path = TEXTURE_PROFILES[fallback_key]
        return {
            "tone": fallback_key,
            "name": fallback_path.name,
            "path": str(fallback_path),
            "exists": fallback_path.exists(),
            "score": None,
            "dominant_bgr": obs["median_bgr"],
            "ranking": [],
        }

    candidates = sorted(candidates, key=lambda x: x["score"])
    best = candidates[0]

    return {
        "tone": best["key"],
        "name": best["name"],
        "path": best["path"],
        "exists": True,
        "score": best["score"],
        "dominant_bgr": obs["median_bgr"],
        "ranking": candidates,
    }


def bgr_to_rgb_list(bgr):
    b, g, r = bgr
    return [int(r), int(g), int(b)]