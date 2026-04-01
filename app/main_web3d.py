import time
import threading
import webbrowser
import cv2

from app.config import CAMERA_INDEX, CONFIDENCE, WINDOW_TITLE, find_model_path
from app.data.instrument_info import INSTRUMENT_INFO
from app.analysis.label_utils import normalize_label
from app.analysis.appearance import (
    crop_from_box,
    choose_best_texture_from_crop,
    bgr_to_rgb_list,
)
from app.detection.detector import InstrumentDetector
from app.ar.overlay import draw_detection_overlay
from app.web.server import run_server
from app.web.state import update_state, reset_state


def start_web_server():
    thread = threading.Thread(
        target=run_server,
        kwargs={"host": "127.0.0.1", "port": 8000},
        daemon=True
    )
    thread.start()
    time.sleep(1.2)


def texture_url_from_profile(texture_profile):
    return f"/assets/textures/{texture_profile['name']}"


def format_ranking(ranking):
    if not ranking:
        return "aucun classement"
    return " | ".join([f"{item['key']}={item['score']}" for item in ranking])


def main():
    try:
        model_path = find_model_path()
    except FileNotFoundError as e:
        print(e)
        return

    print(f"[INFO] Modèle utilisé : {model_path}")

    start_web_server()
    webbrowser.open("http://127.0.0.1:8000")

    detector = InstrumentDetector(str(model_path), conf=CONFIDENCE)

    cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        print("Erreur : impossible d’ouvrir la caméra.")
        return

    print("[INFO] Appuie sur 'q' pour quitter.")

    last_debug_signature = None

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Erreur : impossible de lire l’image caméra.")
            break

        raw_frame = frame.copy()
        results = detector.detect(raw_frame)

        primary_detection = None
        max_area = 0

        for box in results.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            cls = int(box.cls[0])

            raw_label = detector.get_label(cls)
            label = normalize_label(raw_label)
            info_text = INSTRUMENT_INFO.get(label, "Description non disponible.")

            wood_tone = None
            texture_profile = None
            tint_rgb = [181, 141, 107]
            dominant_bgr = None

            if label == "oud":
                crop = crop_from_box(raw_frame, x1, y1, x2, y2)
                texture_profile = choose_best_texture_from_crop(crop)
                wood_tone = texture_profile["tone"]
                dominant_bgr = texture_profile["dominant_bgr"]
                tint_rgb = bgr_to_rgb_list(dominant_bgr)

            frame = draw_detection_overlay(
                frame=frame,
                label=label,
                info_text=info_text,
                box=(x1, y1, x2, y2),
                wood_tone=wood_tone,
                texture_name=texture_profile["name"] if texture_profile else None,
                dominant_color=dominant_bgr,
            )

            area = max(0, (x2 - x1) * (y2 - y1))
            if area > max_area:
                max_area = area
                primary_detection = {
                    "label": label,
                    "info_text": info_text,
                    "wood_tone": wood_tone,
                    "texture_profile": texture_profile,
                    "tint_rgb": tint_rgb,
                }

        if primary_detection is not None:
            if primary_detection["label"] == "oud" and primary_detection["texture_profile"] is not None:
                profile = primary_detection["texture_profile"]

                update_state(
                    visible=True,
                    instrument="oud",
                    history=primary_detection["info_text"],
                    wood_tone=primary_detection["wood_tone"],
                    texture_name=profile["name"],
                    texture_url=texture_url_from_profile(profile),
                    model_url="/assets/models/oud.glb",
                    tint_rgb=primary_detection["tint_rgb"],
                )

                # debug console: afficher seulement quand ça change
                debug_signature = (
                    profile["name"],
                    tuple(primary_detection["tint_rgb"]),
                    profile["score"],
                )

                if debug_signature != last_debug_signature:
                    print("\n[DEBUG OUD]")
                    print(f"Texture choisie : {profile['name']}")
                    print(f"Score meilleur match : {profile['score']}")
                    print(f"Classement : {format_ranking(profile.get('ranking', []))}")
                    last_debug_signature = debug_signature

            else:
                update_state(
                    visible=False,
                    instrument=primary_detection["label"],
                    history=primary_detection["info_text"],
                )
        else:
            reset_state()

        cv2.imshow(WINDOW_TITLE, frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()