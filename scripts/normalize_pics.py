"""Нормализует имена картинок и собирает data/card_images.json."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

root = Path(__file__).resolve().parent.parent
pics = root / "data" / "pics"

# Текущее имя файла (без учёта регистра) -> card_id
CURRENT_TO_ID: dict[str, str] = {
    # Старшие
    "шут.png": "0_shut",
    "маг.png": "1_mag",
    "верховная жрица.png": "2_zhritsa",
    "императрица.png": "3_imperatritsa",
    "император.png": "4_imperator",
    "иерофант.png": "5_ierofant",
    "влюбленные.png": "6_vlyublennye",
    "колесница.png": "7_kolesnitsa",
    "сила.png": "8_sila",
    "отшельник.png": "9_otshelnik",
    "колесо фортуны.png": "10_koleso",
    "справедливость.png": "11_spravedlivost",
    "повешенный.png": "12_poveshennyy",
    "смерть.png": "13_smert",
    "умеренность.png": "14_umerennost",
    "дьявол.png": "15_dyavol",
    "башня.png": "16_bashnya",
    "звезда.png": "17_zvezda",
    "луна.png": "18_luna",
    "солнце.png": "19_solntse",
    "страшный суд.png": "20_sud",
    "мир.png": "21_mir",
    # Мечи
    "туз мечей.png": "swords_ace",
    "2 меч.png": "swords_2",
    "3 мечей.png": "swords_3",
    "4 меч.png": "swords_4",
    "5 меч.png": "swords_5",
    "6 меч.png": "swords_6",
    "7 меч.png": "swords_7",
    "8 меч.png": "swords_8",
    "9 меч.png": "swords_9",
    "10 мечей.png": "swords_10",
    "паж меч.png": "swords_page",
    "рыцарь мечей.png": "swords_knight",
    "королева мечей.png": "swords_queen",
    "король мечей.png": "swords_king",
    # Кубки
    "туз кубк.png": "cups_ace",
    "2 куб.png": "cups_2",
    "3 куб.png": "cups_3",
    "4 куб.png": "cups_4",
    "5 куб.png": "cups_5",
    "6 куб.png": "cups_6",
    "7 куб.png": "cups_7",
    "8 кубк.png": "cups_8",
    "9 куб.png": "cups_9",
    "10 куб.png": "cups_10",
    "паж куб.png": "cups_page",
    "рыцарь кубк.png": "cups_knight",
    "королева кубк.png": "cups_queen",
    "король кубк.png": "cups_king",
    # Жезлы
    "туз жезл.png": "wands_ace",
    "2 жезл.png": "wands_2",
    "3 жезл.png": "wands_3",
    "4 жезлов.png": "wands_4",
    "5 жезлов.png": "wands_5",
    "6 жезл.png": "wands_6",
    "7 жезл.png": "wands_7",
    "8 жезлов.jpg": "wands_8",
    "9 жезл.png": "wands_9",
    "10 жезл.png": "wands_10",
    "паж жезл.png": "wands_page",
    "рыцарь жезл.png": "wands_knight",
    "королева жезл.png": "wands_queen",
    "король жезл.png": "wands_king",
    # Пентакли
    "туз пент.png": "pentacles_ace",
    "2 пент.png": "pentacles_2",
    "3 пент.png": "pentacles_3",
    "4 пент.png": "pentacles_4",
    "5 пент.png": "pentacles_5",
    "6 пент.png": "pentacles_6",
    "7 пент.png": "pentacles_7",
    "8 пент.png": "pentacles_8",
    "9 пент.png": "pentacles_9",
    "10 пент.png": "pentacles_10",
    "паж пент.png": "pentacles_page",
    "рыцарь пент.png": "pentacles_knight",
    "королева пент.png": "pentacles_queen",
    "король пент.png": "pentacles_king",
}

# Единые целевые имена (русские, согласованные)
ID_TO_CANON: dict[str, str] = {
    "0_shut": "шут.png",
    "1_mag": "маг.png",
    "2_zhritsa": "верховная жрица.png",
    "3_imperatritsa": "императрица.png",
    "4_imperator": "император.png",
    "5_ierofant": "иерофант.png",
    "6_vlyublennye": "влюбленные.png",
    "7_kolesnitsa": "колесница.png",
    "8_sila": "сила.png",
    "9_otshelnik": "отшельник.png",
    "10_koleso": "колесо фортуны.png",
    "11_spravedlivost": "справедливость.png",
    "12_poveshennyy": "повешенный.png",
    "13_smert": "смерть.png",
    "14_umerennost": "умеренность.png",
    "15_dyavol": "дьявол.png",
    "16_bashnya": "башня.png",
    "17_zvezda": "звезда.png",
    "18_luna": "луна.png",
    "19_solntse": "солнце.png",
    "20_sud": "страшный суд.png",
    "21_mir": "мир.png",
    "swords_ace": "туз мечей.png",
    "swords_2": "2 мечей.png",
    "swords_3": "3 мечей.png",
    "swords_4": "4 мечей.png",
    "swords_5": "5 мечей.png",
    "swords_6": "6 мечей.png",
    "swords_7": "7 мечей.png",
    "swords_8": "8 мечей.png",
    "swords_9": "9 мечей.png",
    "swords_10": "10 мечей.png",
    "swords_page": "паж мечей.png",
    "swords_knight": "рыцарь мечей.png",
    "swords_queen": "королева мечей.png",
    "swords_king": "король мечей.png",
    "cups_ace": "туз кубков.png",
    "cups_2": "2 кубков.png",
    "cups_3": "3 кубков.png",
    "cups_4": "4 кубков.png",
    "cups_5": "5 кубков.png",
    "cups_6": "6 кубков.png",
    "cups_7": "7 кубков.png",
    "cups_8": "8 кубков.png",
    "cups_9": "9 кубков.png",
    "cups_10": "10 кубков.png",
    "cups_page": "паж кубков.png",
    "cups_knight": "рыцарь кубков.png",
    "cups_queen": "королева кубков.png",
    "cups_king": "король кубков.png",
    "wands_ace": "туз жезлов.png",
    "wands_2": "2 жезлов.png",
    "wands_3": "3 жезлов.png",
    "wands_4": "4 жезлов.png",
    "wands_5": "5 жезлов.png",
    "wands_6": "6 жезлов.png",
    "wands_7": "7 жезлов.png",
    "wands_8": "8 жезлов.jpg",
    "wands_9": "9 жезлов.png",
    "wands_10": "10 жезлов.png",
    "wands_page": "паж жезлов.png",
    "wands_knight": "рыцарь жезлов.png",
    "wands_queen": "королева жезлов.png",
    "wands_king": "король жезлов.png",
    "pentacles_ace": "туз пентаклей.png",
    "pentacles_2": "2 пентаклей.png",
    "pentacles_3": "3 пентаклей.png",
    "pentacles_4": "4 пентаклей.png",
    "pentacles_5": "5 пентаклей.png",
    "pentacles_6": "6 пентаклей.png",
    "pentacles_7": "7 пентаклей.png",
    "pentacles_8": "8 пентаклей.png",
    "pentacles_9": "9 пентаклей.png",
    "pentacles_10": "10 пентаклей.png",
    "pentacles_page": "паж пентаклей.png",
    "pentacles_knight": "рыцарь пентаклей.png",
    "pentacles_queen": "королева пентаклей.png",
    "pentacles_king": "король пентаклей.png",
}


def main() -> None:
    existing = {p.name.lower(): p for p in pics.iterdir() if p.is_file()}
    missing_src: list[str] = []
    unknown: list[str] = []
    mapped: dict[str, Path] = {}

    for name, path in existing.items():
        cid = CURRENT_TO_ID.get(name)
        if not cid:
            unknown.append(path.name)
            continue
        mapped[cid] = path

    for src_name, cid in CURRENT_TO_ID.items():
        if cid not in mapped:
            missing_src.append(src_name)

    expected_ids = set(ID_TO_CANON)
    got_ids = set(mapped)
    missing_ids = sorted(expected_ids - got_ids)
    extra_ids = sorted(got_ids - expected_ids)

    report_lines = [
        f"files_on_disk={len(existing)}",
        f"mapped={len(mapped)}",
        f"missing_sources={missing_src}",
        f"unknown_files={unknown}",
        f"missing_ids={missing_ids}",
        f"extra_ids={extra_ids}",
    ]
    (root / "data" / "_pics_check.txt").write_text(
        "\n".join(report_lines), encoding="utf-8"
    )

    if missing_src or unknown or missing_ids:
        raise SystemExit("Mapping incomplete. See data/_pics_check.txt")

    # Двухфазный rename через temp, чтобы не затереть файлы
    tmp_dir = pics / "_tmp_rename"
    if tmp_dir.exists():
        shutil.rmtree(tmp_dir)
    tmp_dir.mkdir()

    id_to_tmp: dict[str, Path] = {}
    for cid, src in mapped.items():
        ext = src.suffix.lower()
        canon = ID_TO_CANON[cid]
        # сохранить исходное расширение, если канон не совпал (jpg)
        if Path(canon).suffix.lower() != ext:
            canon = str(Path(canon).with_suffix(ext))
            ID_TO_CANON[cid] = canon
        tmp_path = tmp_dir / f"{cid}{ext}"
        shutil.copy2(src, tmp_path)
        id_to_tmp[cid] = tmp_path

    # удалить старые (кроме tmp)
    for path in list(pics.iterdir()):
        if path.is_file():
            path.unlink()

    card_images: dict[str, str] = {}
    for cid, tmp_path in id_to_tmp.items():
        dest_name = ID_TO_CANON[cid]
        dest = pics / dest_name
        shutil.move(str(tmp_path), str(dest))
        card_images[cid] = dest_name

    shutil.rmtree(tmp_dir)

    # стабильный порядок
    ordered = {k: card_images[k] for k in ID_TO_CANON if k in card_images}
    (root / "data" / "card_images.json").write_text(
        json.dumps(ordered, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    # сверка с day_cards
    day_cards = json.loads((root / "data" / "day_cards.json").read_text(encoding="utf-8"))
    day_ids = {c["id"] for c in day_cards}
    missing_for_day = sorted(day_ids - set(ordered))
    extra_for_day = sorted(set(ordered) - day_ids)
    final = [
        f"OK renamed={len(ordered)}",
        f"day_cards={len(day_ids)}",
        f"missing_for_day_cards={missing_for_day}",
        f"extra_vs_day_cards={extra_for_day}",
    ]
    (root / "data" / "_pics_check.txt").write_text("\n".join(final), encoding="utf-8")
    print("\n".join(final))


if __name__ == "__main__":
    main()
