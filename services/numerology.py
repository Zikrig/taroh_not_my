"""Расчёт энергии года / денежного прогноза по дате рождения."""

from __future__ import annotations

from datetime import date


def digit_sum_of_number(n: int) -> int:
    return sum(int(ch) for ch in str(abs(n)))


def calc_energy_number(birth: date, year: int) -> int:
    """Сумма цифр дня + месяца + года. Пока > 22 — вычитаем 22. 0 → 22 (Шут)."""
    total = digit_sum_of_number(birth.day) + digit_sum_of_number(birth.month)
    total += digit_sum_of_number(year)
    while total > 22:
        total -= 22
    if total == 0:
        return 22
    return total


def parse_birth_date(text: str) -> date | None:
    """Принимает ДД.ММ.ГГГГ или ДД.ММ (год подставляется условно 2000)."""
    text = (text or "").strip().replace("/", ".").replace("-", ".")
    parts = [p for p in text.split(".") if p]
    if len(parts) == 2:
        day_s, month_s = parts
        year = 2000
    elif len(parts) == 3:
        day_s, month_s, year_s = parts
        if not year_s.isdigit() or len(year_s) not in (2, 4):
            return None
        year = int(year_s)
        if year < 100:
            year += 2000 if year < 30 else 1900
    else:
        return None
    if not (day_s.isdigit() and month_s.isdigit()):
        return None
    day, month = int(day_s), int(month_s)
    try:
        return date(year, month, day)
    except ValueError:
        return None
