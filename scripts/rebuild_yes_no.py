import json
import re
from pathlib import Path

root = Path(__file__).resolve().parent.parent
yn = (root / "_extracted" / "ДА_или_нет.txt").read_text(encoding="utf-8")

major_names = {
    0: "Шут",
    1: "Маг",
    2: "Верховная Жрица",
    3: "Императрица",
    4: "Император",
    5: "Иерофант",
    6: "Влюблённые",
    7: "Колесница",
    8: "Сила",
    9: "Отшельник",
    10: "Колесо Фортуны",
    11: "Справедливость",
    12: "Повешенный",
    13: "Смерть",
    14: "Умеренность",
    15: "Дьявол",
    16: "Башня",
    17: "Звезда",
    18: "Луна",
    19: "Солнце",
    20: "Суд",
    21: "Мир",
}
roman_map = {
    "I": 1,
    "II": 2,
    "III": 3,
    "IV": 4,
    "V": 5,
    "VI": 6,
    "VII": 7,
    "VIII": 8,
    "IX": 9,
    "X": 10,
    "XI": 11,
    "XII": 12,
    "XIII": 13,
    "XIV": 14,
    "XV": 15,
    "XVI": 16,
    "XVII": 17,
    "XVIII": 18,
    "XIX": 19,
    "XX": 20,
    "XXI": 21,
}

pat = re.compile(r"(?m)^(?:Шут\b|([IVX]+)\.\s*[^\n]*)")
matches = list(pat.finditer(yn))
answer_re = re.compile(
    r"^(Да|Нет|Пока не ясно|Скорее да|Скорее нет|Вероятнее всего да)\s*[—\-]?\s*(.*)$",
    re.I | re.S,
)

yesno = []
for i, m in enumerate(matches):
    start = m.start()
    end = matches[i + 1].start() if i + 1 < len(matches) else len(yn)
    block = yn[start:end].strip()
    first_line = block.split("\n", 1)[0].strip()
    rest = block.split("\n", 1)[1].strip() if "\n" in block else ""

    if first_line.startswith("Шут"):
        num = 0
        after = first_line[len("Шут") :].strip()
        body = (after + "\n" + rest).strip() if after else rest
    else:
        rm = re.match(r"^([IVX]+)\.\s*(.*)$", first_line)
        num = roman_map[rm.group(1)]
        after = rm.group(2).strip()
        for variant in [
            major_names[num],
            major_names[num].replace("ё", "е"),
            "Жрица",
            "Верховная Жрица",
            "Влюбленные",
            "Страшный Суд",
            "Суд",
        ]:
            if after.startswith(variant):
                after = after[len(variant) :].strip()
                break
        after = re.sub(r"^[\U0001F300-\U0001FAFF\s]+", "", after)
        body = (after + "\n" + rest).strip() if after else rest

    body = re.sub(r"\s+", " ", body).strip()
    am = answer_re.match(body)
    answer = am.group(1) if am else ""
    yesno.append(
        {
            "number": num,
            "name": major_names[num],
            "answer": answer,
            "text": body,
        }
    )

(root / "data" / "yes_no.json").write_text(
    json.dumps(yesno, ensure_ascii=False, indent=2), encoding="utf-8"
)
report = "\n".join(f"{y['number']:2} {y['name']}: [{y['answer']}]" for y in yesno)
(root / "data" / "_yesno_check.txt").write_text(report, encoding="utf-8")
print("count", len(yesno))
