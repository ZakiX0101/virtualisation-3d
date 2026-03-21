from pathlib import Path
import shutil

val_dir = Path("Dataset/labels/val")
backup_dir = Path("Dataset/labels/val_backup_before_correct_fix")

# Sauvegarde de securite
if not backup_dir.exists():
    shutil.copytree(val_dir, backup_dir)
    print(f"[OK] Backup cree: {backup_dir}")
else:
    print(f"[INFO] Backup existe deja: {backup_dir}")

# Mapping correct pour val seulement
class_map = {
    "0": "1",  # bendir -> 1
    "1": "2",  # guembri -> 2
    "2": "0",  # oud -> 0
    "3": "3",  # outar -> 3
}

file_count = 0

for file in val_dir.glob("*.txt"):
    file_count += 1
    lines = file.read_text(encoding="utf-8").splitlines()
    new_lines = []

    for line in lines:
        parts = line.strip().split()
        if len(parts) < 5:
            continue

        cls_id = parts[0]
        if cls_id in class_map:
            parts[0] = class_map[cls_id]

        new_lines.append(" ".join(parts))

    file.write_text("\n".join(new_lines) + ("\n" if new_lines else ""), encoding="utf-8")

print(f"[OK] {file_count} fichiers traites dans {val_dir}")
print("[OK] Mapping applique uniquement sur val")