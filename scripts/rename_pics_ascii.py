"""Переименовать data/pics в ASCII-имена по card_images.json."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

root = Path(__file__).resolve().parent.parent
pics = root / "data" / "pics"
mapping_path = root / "data" / "card_images.json"
mapping: dict[str, str] = json.loads(mapping_path.read_text(encoding="utf-8"))

tmp = pics / "_tmp_ascii"
if tmp.exists():
    shutil.rmtree(tmp)
tmp.mkdir()

new_mapping: dict[str, str] = {}
missing: list[str] = []

for card_id, old_name in mapping.items():
    src = pics / old_name
    if not src.exists():
        # уже ascii?
        if (pics / f"{card_id}{Path(old_name).suffix}").exists():
            new_mapping[card_id] = f"{card_id}{Path(old_name).suffix}"
            continue
        missing.append(old_name)
        continue
    ext = src.suffix.lower() or ".png"
    new_name = f"{card_id}{ext}"
    shutil.copy2(src, tmp / new_name)
    new_mapping[card_id] = new_name

if missing:
    raise SystemExit(f"Missing files: {missing}")

for p in pics.iterdir():
    if p.is_file():
        p.unlink()

for p in tmp.iterdir():
    shutil.move(str(p), str(pics / p.name))
shutil.rmtree(tmp)

mapping_path.write_text(
    json.dumps(new_mapping, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)
print(f"OK renamed {len(new_mapping)} files to ASCII ids")
