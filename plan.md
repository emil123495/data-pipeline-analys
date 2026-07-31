# 🌤️ Weather Forecast Accuracy Pipeline 

## Opis projektu

Zautomatyzowany pipeline danych, który **co godzinę** odpytuje Forecast API i zapisuje całą zwróconą odpowiedź czyli zarówno dane na "teraz" (najkrótsze możliwe wyprzedzenie), jak i prognozę na kolejne dni. Dzięki temu, zbierając dane przez dłuższy czas, można porównać to, co model przewidział z wyprzedzeniem, z tym, co model "widział" jako aktualny stan w danym momencie — i policzyć, jak błąd prognozy rośnie wraz z wydłużającym się horyzontem czasowym (lead time).


**Źródło danych:** [Open-Meteo Forecast API](https://open-meteo.com/) — darmowe, bez klucza autoryzacyjnego

**Stack technologiczny:** Python, Pandas, SQLite → PostgreSQL (Docker), Streamlit, cron/GitHub Actions

---

## Jak to działa (logika kluczowa dla projektu)

Co godzinę skrypt:
1. Odpytuje Forecast API dla wszystkich miast — dostaje **jedną odpowiedź** zawierającą serię godzinową (np. najbliższe 168h/7 dni)
2. Dla każdego rekordu w tej serii liczy `lead_time_hours = target_time - fetch_time`
3. Rekord z `lead_time_hours = 0` (albo najmniejszy dostępny, np. bieżąca pełna godzina) trafia **dodatkowo** do tabeli `fact_actual`
4. Wszystkie rekordy (poza lead_time=0) trafiają do `fact_forecast`

Efekt: z czasem `fact_forecast` gromadzi wiele "wersji" prognozy dla tego samego `target_time`, zrobionych z różnym wyprzedzeniem, a `fact_actual` gromadzi jedną wartość "faktyczną" per godzina. Łącząc je po `(city_id, target_time)`, dostajesz błąd prognozy w funkcji lead_time.

---

## Architektura danych

```
                 ┌──────────────────────┐
                 │   Forecast API         │
                 │   (odpytywane co godz.) │
                 └───────────┬───────────┘
                             ▼
                 data/raw/YYYY/MM/DD/
                 weather_HH-MM.json.gz
                             │
                             ▼
              ┌─────────────────────────┐
              │  TRANSFORM (Pandas)       │
              │  - walidacja, czyszczenie  │
              │  - liczenie lead_time_hours │
              │  - rozdzielenie: lead=0     │
              │    → actual, reszta         │
              │    → forecast                │
              └─────────────┬────────────┘
                             ▼
              ┌───────────────────────┐
              │  fact_forecast          │  (wiele wersji prognozy
              │  fact_actual             │   dla tego samego target_time)
              │  dim_cities               │
              └─────────────┬────────────┘
                             ▼
              ┌───────────────────────┐
              │  JOIN po (city_id,       │
              │  target_time) → error     │
              └─────────────┬────────────┘
                             ▼
                    ┌──────────────┐
                    │  Streamlit    │
                    │  Dashboard    │
                    └──────────────┘
```

---

## Model danych

### `dim_cities`
| kolumna | typ | opis |
|---|---|---|
| city_id | INTEGER PK | |
| city_name | TEXT | np. "Warszawa" |
| latitude | REAL | |
| longitude | REAL | |
| country | TEXT | |

### `fact_forecast`
| kolumna | typ | opis |
|---|---|---|
| id | INTEGER PK | |
| city_id | INTEGER FK | |
| target_time | DATETIME | godzina, której dotyczy dany punkt danych |
| fetch_time | DATETIME | kiedy zapytanie do API zostało wykonane |
| lead_time_hours | INTEGER | target_time − fetch_time, **kluczowa zmienna analityczna** |
| temperature_2m | REAL | |
| precipitation | REAL | |
| wind_speed_10m | REAL | |
| ... | | pozostałe zmienne wg potrzeb |

`UNIQUE(city_id, target_time, fetch_time)` — jeden rekord na kombinację miasto + godzina docelowa + moment zapytania.

### `fact_actual`
| kolumna | typ | opis |
|---|---|---|
| id | INTEGER PK | |
| city_id | INTEGER FK | |
| observed_time | DATETIME | = target_time rekordu, który miał lead_time≈0 w momencie zapisu |
| temperature_2m | REAL | |
| precipitation | REAL | |
| wind_speed_10m | REAL | |
| ... | | |

`UNIQUE(city_id, observed_time)` — jedna wartość "faktyczna" na godzinę i miasto (nawet jeśli teoretycznie różne zapytania mogłyby dać nieco inny wynik dla lead_time=0, bierzemy pierwszy/najbliższy zapis).

### Zapytanie analityczne: `forecast_error`
```sql
SELECT
    f.city_id,
    f.lead_time_hours,
    f.temperature_2m AS predicted,
    a.temperature_2m AS actual,
    (f.temperature_2m - a.temperature_2m) AS error,
    ABS(f.temperature_2m - a.temperature_2m) AS abs_error
FROM fact_forecast f
JOIN fact_actual a
    ON f.city_id = a.city_id
    AND f.target_time = a.observed_time
```
Grupowane po `lead_time_hours` (lub zaokrąglone do dni: `lead_time_hours / 24`) → główny wykres dashboardu.

---

## Fazy projektu

### 🚀 Faza V1 — Fundament (lokalny skrypt)

**Cel:** Jedno źródło API, poprawny podział na forecast/actual, brak duplikatów.

**Extract**
- [ ] Struktura folderów: `data/raw/YYYY/MM/DD/`, partycjonowane po dacie pobrania
- [ ] Plik konfiguracyjny `cities.json` (nazwa, lat, long, kraj)
- [ ] Funkcja `fetch_weather()` — jedno zapytanie do Forecast API dla wszystkich miast na raz (Open-Meteo obsługuje wiele lokalizacji w jednym requeście)
- [ ] Zapis surowego JSON-a

**Transform**
- [ ] Wczytanie i spłaszczenie odpowiedzi do DataFrame
- [ ] Dodanie nazw miast (join z `cities.json`)
- [ ] Obliczenie `fetch_time` (kiedy zrobiono zapytanie) i `lead_time_hours` dla każdego rekordu (`target_time - fetch_time`)
- [ ] Walidacja zakresów (temperatura, wilgotność, opady) — **z logowaniem**, ile rekordów odrzucono/obcięto, nie cichy `clip()`
- [ ] Obsługa braków danych (decyzja: interpolacja / odrzucenie / flaga)
- [ ] Rozdzielenie DataFrame na dwie części: `lead_time_hours == 0` (lub najmniejszy dostępny) → kandydat do `fact_actual`; cała reszta → `fact_forecast`
- [ ] Usuwanie duplikatów na poziomie DataFrame przed zapisem

**Load**
- [ ] Schemat SQLite zgodny z modelem powyżej, z `UNIQUE` constraints
- [ ] Zapis przez `INSERT OR IGNORE` (nie `to_sql(if_exists="replace")`!)
- [ ] Test: dwukrotne uruchomienie skryptu w tej samej godzinie nie tworzy duplikatów (idempotencja)

### 📊 Faza V2 — Warstwa analityczna i wizualna

- [ ] Zapytanie SQL/Pandas: JOIN `fact_forecast` z `fact_actual` po `(city_id, target_time = observed_time)`
- [ ] Agregacja błędu po `lead_time_hours` (np. co 24h: dzień 1, dzień 2, ..., dzień 7)
- [ ] Streamlit: wykres główny — oś X = lead_time (dni), oś Y = średni błąd bezwzględny temperatury
- [ ] KPI: "średni błąd prognozy na 24h: X°C", "na 7 dni: Y°C"

### ⚙️ Faza V3 — Wersja inżynierska (pro do CV)

- [ ] Migracja SQLite → PostgreSQL w Dockerze
- [ ] UPSERT (`INSERT ... ON CONFLICT DO UPDATE`) w Postgresie
- [ ] Podział kodu na moduły (`extract.py`, `transform.py`, `load.py`)
- [ ] `requirements.txt`
- [ ] README: diagram architektury, opis problemu i metodologii (w tym zastrzeżenie o "actual = nowcast"), instrukcja uruchomienia, sekcja "czego się nauczyłem"

---