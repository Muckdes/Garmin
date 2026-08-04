"""
Baut garmin_dashboard.html aus den JSON-Exporten von garmin_export.py neu auf.

Nutzung:
    python build_dashboard.py --days 30 --data-dir garmin_data --out garmin_dashboard.html
"""

import argparse
import json
import os

TEMPLATE = """<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Trainings-Dashboard</title>
<style>
  * {{ box-sizing: border-box; }}
  body {{
    font-family: system-ui, -apple-system, sans-serif;
    background: #f7f6f3;
    color: #0b0b0b;
    margin: 0;
    padding: 2rem 1.5rem 4rem;
  }}
  .wrap {{ max-width: 900px; margin: 0 auto; }}
  h1 {{ font-size: 22px; font-weight: 500; margin: 0 0 4px; }}
  .sub {{ font-size: 14px; color: #6b6a66; margin: 0 0 2rem; }}
  .kpis {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    gap: 12px;
    margin-bottom: 2rem;
  }}
  .kpi {{ background: #fff; border: 0.5px solid #e1e0d9; border-radius: 10px; padding: 1rem; }}
  .kpi p:first-child {{ font-size: 13px; color: #6b6a66; margin: 0 0 4px; }}
  .kpi p:last-child {{ font-size: 24px; font-weight: 500; margin: 0; }}
  h2 {{ font-size: 15px; font-weight: 500; margin: 0 0 8px; }}
  .legend {{ display: flex; flex-wrap: wrap; gap: 16px; margin-bottom: 8px; font-size: 12px; color: #6b6a66; }}
  .legend span {{ display: flex; align-items: center; gap: 4px; }}
  .dot {{ width: 10px; height: 10px; border-radius: 2px; display: inline-block; }}
  .chart-box {{ position: relative; width: 100%; height: 220px; margin-bottom: 2.5rem; background: #fff; border: 0.5px solid #e1e0d9; border-radius: 10px; padding: 1rem; }}
  .chart-box.short {{ height: 200px; }}
  .row {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
  @media (max-width: 600px) {{ .row {{ grid-template-columns: 1fr; }} }}
  footer {{ font-size: 12px; color: #9a998f; margin-top: 2rem; }}
</style>
</head>
<body>
<div class="wrap">
  <h1>Trainings-Dashboard</h1>
  <p class="sub">Garmin Connect Export &middot; {date_range} &middot; zuletzt aktualisiert {generated_at}</p>

  <div class="kpis">
    <div class="kpi"><p>Ø Schritte/Tag</p><p>{avg_steps}</p></div>
    <div class="kpi"><p>Ø Ruhepuls</p><p>{avg_rhr} bpm</p></div>
    <div class="kpi"><p>Ø Schlaf</p><p>{avg_sleep} h</p></div>
    <div class="kpi"><p>Ø HRV</p><p>{avg_hrv} ms</p></div>
    <div class="kpi"><p>Trainings</p><p>{n_activities}</p></div>
  </div>

  <h2>Schritte pro Tag</h2>
  <div class="chart-box short"><canvas id="stepsChart"></canvas></div>

  <h2>Ruhepuls und HRV</h2>
  <div class="legend">
    <span><span class="dot" style="background:#2a78d6"></span>Ruhepuls (bpm)</span>
    <span><span class="dot" style="background:#1baf7a"></span>HRV nachts (ms)</span>
  </div>
  <div class="chart-box"><canvas id="hrChart"></canvas></div>

  <h2>Schlafzusammensetzung</h2>
  <div class="legend">
    <span><span class="dot" style="background:#4a3aa7"></span>Tiefschlaf</span>
    <span><span class="dot" style="background:#2a78d6"></span>Leichtschlaf</span>
    <span><span class="dot" style="background:#1baf7a"></span>REM-Schlaf</span>
  </div>
  <div class="chart-box"><canvas id="sleepChart"></canvas></div>

  <div class="row">
    <div>
      <h2>Trainingsverteilung</h2>
      <div class="chart-box short"><canvas id="typeChart"></canvas></div>
    </div>
    <div>
      <h2>Lauftempo (min/km)</h2>
      <div class="chart-box short"><canvas id="paceChart"></canvas></div>
    </div>
  </div>

  <footer>Erstellt aus deinem Garmin-Connect-Export. Alle Daten werden lokal im Browser gerendert, nichts wird hochgeladen.</footer>
</div>

<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<script>
const dates = {dates_json};
const steps = {steps_json};
const rhr = {rhr_json};
const hrv = {hrv_json};
const deep = {deep_json};
const light = {light_json};
const rem = {rem_json};
const typeLabels = {type_labels_json};
const typeCounts = {type_counts_json};
const typeColors = {type_colors_json};
const runDates = {run_dates_json};
const pace = {pace_json};

Chart.defaults.font.family = "system-ui, -apple-system, sans-serif";
Chart.defaults.color = '#6b6a66';
const gridColor = '#e1e0d9';

new Chart(document.getElementById('stepsChart'), {{
  type: 'bar',
  data: {{ labels: dates, datasets: [{{ data: steps, backgroundColor: '#2a78d6', borderRadius: 4, maxBarThickness: 16 }}] }},
  options: {{ responsive: true, maintainAspectRatio: false,
    plugins: {{ legend: {{ display: false }} }},
    scales: {{
      x: {{ grid: {{ display: false }}, ticks: {{ maxRotation: 0, autoSkip: true, maxTicksLimit: 10 }} }},
      y: {{ grid: {{ color: gridColor }} }}
    }}
  }}
}});

new Chart(document.getElementById('hrChart'), {{
  type: 'line',
  data: {{ labels: dates, datasets: [
    {{ label: 'Ruhepuls', data: rhr, borderColor: '#2a78d6', pointRadius: 0, borderWidth: 2, tension: 0.3 }},
    {{ label: 'HRV', data: hrv, borderColor: '#1baf7a', pointRadius: 0, borderWidth: 2, tension: 0.3, borderDash: [5,3] }}
  ]}},
  options: {{ responsive: true, maintainAspectRatio: false,
    plugins: {{ legend: {{ display: false }} }},
    scales: {{
      x: {{ grid: {{ display: false }}, ticks: {{ maxRotation: 0, autoSkip: true, maxTicksLimit: 10 }} }},
      y: {{ grid: {{ color: gridColor }} }}
    }}
  }}
}});

new Chart(document.getElementById('sleepChart'), {{
  type: 'line',
  data: {{ labels: dates, datasets: [
    {{ label: 'Tiefschlaf', data: deep, borderColor: '#4a3aa7', backgroundColor: '#4a3aa71a', fill: true, pointRadius: 0, borderWidth: 1, stack: 's' }},
    {{ label: 'Leichtschlaf', data: light, borderColor: '#2a78d6', backgroundColor: '#2a78d61a', fill: true, pointRadius: 0, borderWidth: 1, stack: 's' }},
    {{ label: 'REM', data: rem, borderColor: '#1baf7a', backgroundColor: '#1baf7a1a', fill: true, pointRadius: 0, borderWidth: 1, stack: 's' }}
  ]}},
  options: {{ responsive: true, maintainAspectRatio: false,
    plugins: {{ legend: {{ display: false }} }},
    scales: {{
      x: {{ stacked: true, grid: {{ display: false }}, ticks: {{ maxRotation: 0, autoSkip: true, maxTicksLimit: 10 }} }},
      y: {{ stacked: true, grid: {{ color: gridColor }}, title: {{ display: true, text: 'Stunden' }} }}
    }}
  }}
}});

new Chart(document.getElementById('typeChart'), {{
  type: 'doughnut',
  data: {{ labels: typeLabels, datasets: [{{
    data: typeCounts,
    backgroundColor: typeColors,
    borderColor: '#fff', borderWidth: 2
  }}] }},
  options: {{ responsive: true, maintainAspectRatio: false,
    plugins: {{ legend: {{ position: 'bottom', labels: {{ boxWidth: 10, font: {{ size: 12 }} }} }} }}
  }}
}});

new Chart(document.getElementById('paceChart'), {{
  type: 'line',
  data: {{ labels: runDates, datasets: [{{ data: pace, borderColor: '#eb6834', pointRadius: 4, pointBackgroundColor: '#eb6834', borderWidth: 2, tension: 0.2 }}] }},
  options: {{ responsive: true, maintainAspectRatio: false,
    plugins: {{ legend: {{ display: false }} }},
    scales: {{
      x: {{ grid: {{ display: false }} }},
      y: {{ grid: {{ color: gridColor }}, title: {{ display: true, text: 'min/km' }} }}
    }}
  }}
}});
</script>
</body>
</html>
"""

TYPE_LABELS_DE = {
    "strength_training": "Krafttraining",
    "running": "Laufen",
    "treadmill_running": "Laufen (Band)",
    "hiit": "HIIT",
    "paddelball": "Padel",
    "cycling": "Radfahren",
    "swimming": "Schwimmen",
    "yoga": "Yoga",
    "walking": "Gehen",
}
TYPE_COLOR_CYCLE = ["#2a78d6", "#eb6834", "#eda100", "#e87ba4", "#1baf7a", "#4a3aa7", "#e34948"]


def load_health(data_dir: str, days: int):
    path = os.path.join(data_dir, f"daily_health_{days}d.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_activities(data_dir: str, days: int):
    path = os.path.join(data_dir, f"activities_{days}d.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def build(days: int, data_dir: str, out_path: str):
    health = sorted(load_health(data_dir, days), key=lambda e: e["date"])
    activities = load_activities(data_dir, days)

    dates, steps, rhr, hrv, deep, light, rem = [], [], [], [], [], [], []
    for e in health:
        dates.append(e["date"][5:])
        steps.append(sum((s.get("steps") or 0) for s in (e.get("steps") or [])))
        hr = e.get("heart_rate") or {}
        rhr.append(hr.get("restingHeartRate"))
        sleep = e.get("sleep") or {}
        dto = sleep.get("dailySleepDTO") or {}
        deep.append(round((dto.get("deepSleepSeconds") or 0) / 3600, 2))
        light.append(round((dto.get("lightSleepSeconds") or 0) / 3600, 2))
        rem.append(round((dto.get("remSleepSeconds") or 0) / 3600, 2))
        hrv.append(sleep.get("avgOvernightHrv"))

    valid_steps = [s for s in steps if s is not None]
    valid_rhr = [v for v in rhr if v is not None]
    valid_hrv = [v for v in hrv if v is not None]
    sleep_totals = [d + l + r for d, l, r in zip(deep, light, rem) if (d + l + r) > 0]

    avg_steps = round(sum(valid_steps) / len(valid_steps)) if valid_steps else 0
    avg_rhr = round(sum(valid_rhr) / len(valid_rhr), 1) if valid_rhr else 0
    avg_hrv = round(sum(valid_hrv) / len(valid_hrv), 1) if valid_hrv else 0
    avg_sleep = round(sum(sleep_totals) / len(sleep_totals), 2) if sleep_totals else 0

    type_counts = {}
    run_dates, pace = [], []
    for a in sorted(activities, key=lambda a: a["startTimeLocal"]):
        t = a["activityType"]["typeKey"]
        type_counts[t] = type_counts.get(t, 0) + 1
        if t in ("running", "treadmill_running"):
            dist_km = (a.get("distance") or 0) / 1000
            dur_min = (a.get("duration") or 0) / 60
            if dist_km > 0:
                run_dates.append(a["startTimeLocal"][5:10])
                pace.append(round(dur_min / dist_km, 2))

    type_labels = [TYPE_LABELS_DE.get(t, t) for t in type_counts]
    type_values = list(type_counts.values())
    type_colors = [TYPE_COLOR_CYCLE[i % len(TYPE_COLOR_CYCLE)] for i in range(len(type_counts))]

    date_range = f"{dates[0]} – {dates[-1]}" if dates else ""
    from datetime import datetime

    html = TEMPLATE.format(
        date_range=date_range,
        generated_at=datetime.now().strftime("%d.%m.%Y %H:%M"),
        avg_steps=f"{avg_steps:,}".replace(",", "."),
        avg_rhr=avg_rhr,
        avg_sleep=str(avg_sleep).replace(".", ","),
        avg_hrv=avg_hrv,
        n_activities=len(activities),
        dates_json=json.dumps(dates),
        steps_json=json.dumps(steps),
        rhr_json=json.dumps(rhr),
        hrv_json=json.dumps(hrv),
        deep_json=json.dumps(deep),
        light_json=json.dumps(light),
        rem_json=json.dumps(rem),
        type_labels_json=json.dumps(type_labels),
        type_counts_json=json.dumps(type_values),
        type_colors_json=json.dumps(type_colors),
        run_dates_json=json.dumps(run_dates),
        pace_json=json.dumps(pace),
    )

    out_dir = os.path.dirname(out_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Dashboard aktualisiert -> {out_path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=30)
    parser.add_argument("--data-dir", default="garmin_data")
    parser.add_argument("--out", default="garmin_dashboard.html")
    args = parser.parse_args()
    build(args.days, args.data_dir, args.out)


if __name__ == "__main__":
    main()
