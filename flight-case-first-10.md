# Flight case — первые 10 кейсов (из 50 в v1)

## Задача для Claude Code
Выгрузить данные NTSB по 10 кейсам ниже и сохранить каждый в едином формате, чтобы по нему потом собиралась страница кейса.

Источники: только NTSB (CAROL — carol.ntsb.gov, база avdata — data.ntsb.gov/avdata, docket). aviation-safety.net не использовать.

Для каждого кейса сохранить `data/cases/<ntsb-number>.json` с полями:
- ntsb_number, date, location (город, штат, координаты)
- aircraft (тип, регистрация), operator, flight_type (Part 91 / 121 / 135)
- fatalities, injuries
- report_status: preliminary | final | pending
- narrative (текст NTSB как есть)
- probable_cause (только если final, дословно)
- phase_of_flight, weather
- links: отчёт, docket

Если номер NTSB не указан — найти по дате, месту и типу ВС.
Если данных нет (например, preliminary ещё не вышел) — ставить report_status: pending, причину не придумывать.

## Кейсы

| # | Кейс | Дата | Тип ВС | Статус |
|---|------|------|--------|--------|
| 1 | Kobe Bryant, Калабасас, CA | 2020-01-26 | Sikorsky S-76B | final |
| 2 | US Airways 1549, Гудзон, NY | 2009-01-15 | Airbus A320 | final |
| 3 | Colgan Air 3407, Buffalo, NY | 2009-02-12 | Bombardier Q400 | final |
| 4 | American Eagle 5342 / Black Hawk PAT25, DCA (DCA25MA108) | 2025-01-29 | CRJ700 + UH-60 | final |
| 5 | Greg Biffle, Statesville, NC | 2025-12-18 | Cessna Citation 550 | preliminary |
| 6 | NewsChopper4 (NBC4/Telemundo 52), Chatsworth, CA | 2026-09-15 | Eurocopter AS350 B2 | pending (preliminary ожидается ~середина октября 2026) |
| 7 | Roy Halladay, Мексиканский залив, FL | 2017-11-07 | ICON A5 | final |
| 8 | Свежий Cessna 172 | последние 1–2 года | Cessna 172 | final |
| 9 | Свежий Cirrus SR22 | последние 1–2 года | Cirrus SR22 | final |
| 10 | Свежий Piper PA-28 | последние 1–2 года | Piper PA-28 | final |

Для 8–10: выбрать в CAROL кейсы с final-отчётом за последние 1–2 года, с одной из частых причин (потеря управления, выработка топлива, VFR в IMC). Предложить 2–3 варианта на каждый тип, решение за мной.

## Позже
UPS 2976 (MD-11, Луисвилл, 2025-11-04) — в список остальных 40.
