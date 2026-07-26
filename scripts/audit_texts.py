"""Сверка текстов карт с materials/_extracted."""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

root = Path(__file__).resolve().parent.parent
report: list[str] = []


def load_json(name: str):
    return json.loads((root / "data" / name).read_text(encoding="utf-8"))


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


day = load_json("day_cards.json")
yn = load_json("yes_no.json")
ey = load_json("energy_year.json")
mf = load_json("money_forecast.json")

src_day = norm((root / "_extracted" / "арканы.txt").read_text(encoding="utf-8"))
src_yn = norm((root / "_extracted" / "ДА_или_нет.txt").read_text(encoding="utf-8"))
src_ey = norm((root / "_extracted" / "Энергия_года_1.txt").read_text(encoding="utf-8"))
src_mf = norm((root / "_extracted" / "энергия_денег.txt").read_text(encoding="utf-8"))

report.append(
    f"counts day={len(day)} yes_no={len(yn)} energy={len(ey)} money={len(mf)}"
)

ids = [c["id"] for c in day]
dups = [k for k, v in Counter(ids).items() if v > 1]
report.append(f"day unique={len(set(ids))} dups={dups}")
report.append(
    f"day missing advice: {[c['id'] for c in day if not (c.get('advice') or '').strip()]}"
)
report.append(
    f"day missing text: {[c['id'] for c in day if not (c.get('text') or '').strip()]}"
)

# Expected 78 day cards
expected_major = {f"{i}_" for i in range(22)}  # rough
report.append(f"day majors: {sum(1 for c in day if c.get('kind')=='major')}")
report.append(f"day minors: {sum(1 for c in day if c.get('kind')=='minor')}")


def not_in_source(items, src, sample_fn):
    bad = []
    for item in items:
        sample = sample_fn(item)
        if sample and sample not in src:
            bad.append(item)
    return bad


def day_sample(c):
    t = norm(c["text"])
    return t[25:85] if len(t) > 85 else t[:50]


bad_day = not_in_source(day, src_day, day_sample)
report.append(f"day phrases missing from source: {len(bad_day)}")
for c in bad_day[:20]:
    report.append(f"  day? {c['id']} | {c['name']} | {day_sample(c)[:60]}")

# advice
adv_bad = []
for c in day:
    adv = norm(c.get("advice") or "").rstrip(".")
    if not adv:
        continue
    if adv not in src_day and adv[:50] not in src_day:
        adv_bad.append((c["id"], adv[:70]))
report.append(f"advice missing from source: {len(adv_bad)}")
for a in adv_bad[:15]:
    report.append(f"  adv? {a[0]} | {a[1]}")

# yes_no
report.append(f"yes_no numbers: {sorted(y['number'] for y in yn)}")
report.append(
    f"yes_no empty answers: {[y['name'] for y in yn if not (y.get('answer') or '').strip()]}"
)


def yn_sample(y):
    t = norm(y["text"])
    return t[30:95] if len(t) > 95 else t[10:60]


bad_yn = not_in_source(yn, src_yn, yn_sample)
report.append(f"yes_no phrases missing from source: {len(bad_yn)}")
for y in bad_yn[:15]:
    report.append(f"  yn? {y['number']} {y['name']} | {yn_sample(y)[:60]}")

# energy / money
for label, items, src in (
    ("energy", ey, src_ey),
    ("money", mf, src_mf),
):
    bad = []
    for e in items:
        t = norm(e["text"])
        sample = t[50:120] if len(t) > 120 else t[20:70]
        if sample and sample not in src:
            bad.append((e["number"], e["name"], sample[:55], len(t)))
    report.append(f"{label} phrases missing from source: {len(bad)}")
    for b in bad[:12]:
        report.append(f"  {label}? {b}")

# typos / content issues
TYPOS = [
    "своём желание",
    "своем желание",
    "риятные",
    "соотведствующ",
    "предствален",
    "представленн",
]
for label, items in (("day", day), ("yes_no", yn), ("energy", ey), ("money", mf)):
    for item in items:
        blob = " ".join(
            str(item.get(k, "")) for k in ("text", "advice", "name", "answer")
        )
        for typo in TYPOS:
            if typo in blob:
                key = item.get("id") or item.get("number")
                report.append(f"TYPO {label} {key}: {typo}")

# truncated-looking
for c in day:
    t = norm(c["text"])
    if len(t) < 60:
        report.append(f"SHORT day {c['id']}: {len(t)} | {t[:80]}")
    if t.endswith((" и", " а", " на", " с", " в", " к", " —", "-")):
        report.append(f"TRUNC day {c['id']}: ...{t[-40:]}")

for y in yn:
    t = norm(y["text"])
    if len(t) < 60:
        report.append(f"SHORT yn {y['number']}: {len(t)}")

# length stats
for label, items in (("day", day), ("yes_no", yn), ("energy", ey), ("money", mf)):
    lengths = [len(norm(x["text"])) for x in items]
    report.append(
        f"{label} len min/max/avg = {min(lengths)}/{max(lengths)}/{sum(lengths)//len(lengths)}"
    )

# Show a few suspicious day cards: text without Совет split leftover
for c in day:
    if "Совет:" in c["text"]:
        report.append(f"ADVICE_LEFT_IN_TEXT {c['id']}")

out = root / "data" / "_text_audit.txt"
out.write_text("\n".join(report), encoding="utf-8")
print(out.read_text(encoding="utf-8"))
