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
from app.web.state import update_state


MODEL_BY_INSTRUMENT = {
    "oud": "/assets/models/oud.glb",
    # add others later:
    # "loutar": "/assets/models/loutar.glb",
}


def start_web_server():
    thread = threading.Thread(
        target=run_server,
        kwargs={"host": "127.0.0.1", "port": 8000},
        daemon=True,
    )
    thread.start()
    time.sleep(1.2)


def texture_url_from_profile(texture_profile):
    texture_name = texture_profile["name"]
    return f"/assets/textures/{texture_name}"


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

    last_3d_instrument = None
    last_3d_model_url = None
    last_3d_texture_url = None
    last_3d_texture_name = None
    last_3d_wood_tone = None
    last_3d_tint_rgb = [181, 141, 107]
    last_history = "En attente de détection..."

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
            dominant_color = None
            tint_rgb = [181, 141, 107]

            if label == "oud":
                crop = crop_from_box(raw_frame, x1, y1, x2, y2)
                texture_profile = choose_best_texture_from_crop(crop)
                wood_tone = texture_profile["tone"]
                dominant_color = texture_profile["dominant_bgr"]
                tint_rgb = bgr_to_rgb_list(dominant_color)

            frame = draw_detection_overlay(
                frame=frame,
                label=label,
                info_text=info_text,
                box=(x1, y1, x2, y2),
                wood_tone=wood_tone,
                texture_name=texture_profile["name"] if texture_profile else None,
                dominant_color=dominant_color,
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
            label = primary_detection["label"]
            info_text = primary_detection["info_text"]
            last_history = info_text

            model_url = MODEL_BY_INSTRUMENT.get(label)

            # Changer l'objet 3D seulement si cet instrument a un modèle 3D
            if model_url:
                last_3d_instrument = label
                last_3d_model_url = model_url

                if label == "oud" and primary_detection["texture_profile"] is not None:
                    profile = primary_detection["texture_profile"]
                    last_3d_texture_name = profile["name"]
                    last_3d_texture_url = texture_url_from_profile(profile)
                    last_3d_wood_tone = primary_detection["wood_tone"]
                    last_3d_tint_rgb = primary_detection["tint_rgb"]
                else:
                    last_3d_texture_name = None
                    last_3d_texture_url = None
                    last_3d_wood_tone = None
                    last_3d_tint_rgb = [181, 141, 107]

            # Garder le dernier modèle 3D affiché même si la détection courante
            # n'a pas encore de modèle 3D
            update_state(
                visible=last_3d_model_url is not None,
                instrument=label,  # texte UI = instrument détecté actuellement
                history=last_history,
                wood_tone=last_3d_wood_tone,
                texture_name=last_3d_texture_name,
                texture_url=last_3d_texture_url,
                model_url=last_3d_model_url,
                tint_rgb=last_3d_tint_rgb,
            )

        else:
            # Aucune détection : garder le dernier modèle 3D visible
            update_state(
                visible=last_3d_model_url is not None,
                instrument=last_3d_instrument,
                history=last_history,
                wood_tone=last_3d_wood_tone,
                texture_name=last_3d_texture_name,
                texture_url=last_3d_texture_url,
                model_url=last_3d_model_url,
                tint_rgb=last_3d_tint_rgb,
            )

        cv2.imshow(WINDOW_TITLE, frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()