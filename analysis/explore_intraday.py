from pathlib import Path
import json

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# --------------------------------------------------
# PATHS
# --------------------------------------------------

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT_DIR / "data" / "NIFTY_50_minute.csv"
PLOTS_DIR = ROOT_DIR / "plots"

PLOTS_DIR.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------

df = pd.read_csv(DATA_PATH)

df["date"] = pd.to_datetime(
    df["date"],
    format="%d-%m-%Y %H:%M",
    errors="coerce"
)

df = df.dropna(subset=["date"]).sort_values("date")

df = df[
    (df["date"] >= "2022-01-01") &
    (df["date"] < "2023-01-01")
].copy()

for col in ["open", "high", "low", "close", "volume"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

df = df.dropna(
    subset=["open", "high", "low", "close", "volume"]
)

df["day"] = df["date"].dt.strftime("%Y-%m-%d")

if df.empty:
    raise ValueError("No valid NIFTY 50 data found for 2022.")

# Store every available trading date.
available_dates = sorted(df["day"].unique().tolist())

# Serialize the data for the browser.
records = []

for day, group in df.groupby("day", sort=True):
    records.append({
        "day": day,
        "date": group["date"].dt.strftime("%Y-%m-%d %H:%M:%S").tolist(),
        "open": group["open"].tolist(),
        "high": group["high"].tolist(),
        "low": group["low"].tolist(),
        "close": group["close"].tolist(),
        "volume": group["volume"].tolist()
    })


# --------------------------------------------------
# CREATE INITIAL CHART
# --------------------------------------------------

initial_day = available_dates[0]
initial = next(r for r in records if r["day"] == initial_day)

fig = make_subplots(
    rows=2,
    cols=1,
    shared_xaxes=True,
    vertical_spacing=0.04,
    row_heights=[0.75, 0.25],
    subplot_titles=("NIFTY 50 Price", "Volume")
)

fig.add_trace(
    go.Candlestick(
        x=initial["date"],
        open=initial["open"],
        high=initial["high"],
        low=initial["low"],
        close=initial["close"],
        name="NIFTY 50"
    ),
    row=1,
    col=1
)

fig.add_trace(
    go.Bar(
        x=initial["date"],
        y=initial["volume"],
        name="Volume"
    ),
    row=2,
    col=1
)

fig.update_layout(
    title=f"NIFTY 50 Intraday | {initial_day}",
    template="plotly_dark",
    height=800,
    xaxis_rangeslider_visible=False,
    hovermode="x unified"
)

fig.update_yaxes(title_text="Index Level", row=1, col=1)
fig.update_yaxes(title_text="Volume", row=2, col=1)

# Embed the data in the HTML file.
plot_html = fig.to_html(
    full_html=False,
    include_plotlyjs=True,
    div_id="intraday-chart"
)

data_json = json.dumps(records, separators=(",", ":"))

# --------------------------------------------------
# DATE SELECTOR AND CHART UPDATE
# --------------------------------------------------

html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>NIFTY 50 Intraday Explorer</title>
<style>
    body {{
        margin: 0;
        padding: 20px;
        background: #111827;
        color: #f3f4f6;
        font-family: Arial, sans-serif;
    }}

    .controls {{
        display: flex;
        align-items: center;
        gap: 12px;
        flex-wrap: wrap;
        margin-bottom: 16px;
    }}

    input, button {{
        padding: 10px 12px;
        font-size: 15px;
        border-radius: 6px;
        border: 1px solid #4b5563;
    }}

    input {{
        background: #1f2937;
        color: white;
    }}

    button {{
        background: #374151;
        color: white;
        cursor: pointer;
    }}

    button:hover {{
        background: #4b5563;
    }}

    #status {{
        color: #9ca3af;
        margin-bottom: 12px;
    }}
</style>
</head>

<body>

<h2>NIFTY 50 | Intraday Explorer | 2022</h2>

<div class="controls">
    <label for="datePicker">Select trading date:</label>
    <input type="date"
           id="datePicker"
           min="2022-01-01"
           max="2022-12-31"
           value="{initial_day}">

    <button id="previousDay">← Previous session</button>
    <button id="nextDay">Next session →</button>
</div>

<div id="status"></div>

{plot_html}

<script>
const allData = {data_json};
const dates = allData.map(item => item.day);

const picker = document.getElementById("datePicker");
const status = document.getElementById("status");

function showDate(day) {{
    const item = allData.find(row => row.day === day);

    if (!item) {{
        status.textContent =
            "No trading data available for " + day +
            ". Choose another date.";
        return;
    }}

    picker.value = day;

    const candleTrace = {{
        x: item.date,
        open: item.open,
        high: item.high,
        low: item.low,
        close: item.close,
        type: "candlestick",
        name: "NIFTY 50",
        xaxis: "x",
        yaxis: "y"
    }};

    const volumeTrace = {{
        x: item.date,
        y: item.volume,
        type: "bar",
        name: "Volume",
        xaxis: "x2",
        yaxis: "y2"
    }};

    Plotly.react(
        "intraday-chart",
        [candleTrace, volumeTrace],
        {{
            title: "NIFTY 50 Intraday | " + day,
            template: "plotly_dark",
            height: 800,
            hovermode: "x unified",
            xaxis: {{
                domain: [0, 1],
                anchor: "y",
                rangeslider: {{ visible: false }}
            }},
            yaxis: {{
                domain: [0.30, 1],
                title: "Index Level"
            }},
            xaxis2: {{
                domain: [0, 1],
                anchor: "y2",
                matches: "x"
            }},
            yaxis2: {{
                domain: [0, 0.20],
                title: "Volume"
            }},
            annotations: [
                {{
                    text: "Volume",
                    x: 0.5,
                    y: 0.23,
                    xref: "paper",
                    yref: "paper",
                    showarrow: false,
                    font: {{ color: "#f3f4f6" }}
                }}
            ],
            margin: {{ t: 70, b: 50, l: 70, r: 30 }}
        }},
        {{ responsive: true }}
    );

    status.textContent =
        item.date.length + " one-minute candles | " + day;
}}

picker.addEventListener("change", () => {{
    showDate(picker.value);
}});

document.getElementById("previousDay").addEventListener("click", () => {{
    const index = dates.indexOf(picker.value);

    if (index > 0) {{
        showDate(dates[index - 1]);
    }}
}});

document.getElementById("nextDay").addEventListener("click", () => {{
    const index = dates.indexOf(picker.value);

    if (index >= 0 && index < dates.length - 1) {{
        showDate(dates[index + 1]);
    }}
}});

showDate("{initial_day}");
</script>

</body>
</html>
"""

output_path = PLOTS_DIR / "intraday_explorer_2022.html"
output_path.write_text(html, encoding="utf-8")

print(f"Available trading sessions: {len(available_dates)}")
print(f"Chart saved to: {output_path}")
