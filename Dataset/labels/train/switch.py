from pathlib import Path

folder = Path("")

for file in folder.glob("*.txt"):
    lines = file.read_text(encoding="utf-8").splitlines()
    new_lines = []

    for line in lines:
        parts = line.strip().split()
        if len(parts) >= 5 and parts[0] == "0":
            parts[0] = "3"
        new_lines.append(" ".join(parts))

    file.write_text("\n".join(new_lines) + ("\n" if new_lines else ""), encoding="utf-8")

print("Labels outar corriges: 1 -> 3")