from pathlib import Path

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
# LOAD AND CLEAN DATA
# --------------------------------------------------

print("Loading NIFTY 50 data...")

df = pd.read_csv(DATA_PATH)

# Parse timestamps using the format in your CSV
df["date"] = pd.to_datetime(
    df["date"],
    format="%d-%m-%Y %H:%M",
    errors="coerce"
)

# Remove rows with invalid timestamps
df = df.dropna(subset=["date"])

# Ensure chronological order
df = df.sort_values("date")

# Remove duplicate timestamps
df = df.drop_duplicates(subset=["date"], keep="last")

# Filter the required backtesting period
df = df[
    (df["date"] >= "2022-01-01") &
    (df["date"] < "2023-01-01")
].copy()

if df.empty:
    raise ValueError("No data found for the year 2022.")

print(f"Rows for 2022: {len(df):,}")
print(f"First timestamp: {df['date'].min()}")
print(f"Last timestamp:  {df['date'].max()}")


# --------------------------------------------------
# CREATE RAW CANDLESTICK CHART
# --------------------------------------------------

fig = make_subplots(
    rows=2,
    cols=1,
    shared_xaxes=True,
    vertical_spacing=0.04,
    row_heights=[0.75, 0.25],
    subplot_titles=("NIFTY 50 Price", "Volume")
)

# Price candles
fig.add_trace(
    go.Candlestick(
        x=df["date"],
        open=df["open"],
        high=df["high"],
        low=df["low"],
        close=df["close"],
        name="NIFTY 50"
    ),
    row=1,
    col=1
)

# Volume bars
fig.add_trace(
    go.Bar(
        x=df["date"],
        y=df["volume"],
        name="Volume"
    ),
    row=2,
    col=1
)

fig.update_layout(
    title="NIFTY 50 | Raw Intraday Data | 2022",
    template="plotly_dark",
    height=850,
    xaxis_rangeslider_visible=False,
    hovermode="x unified"
)

fig.update_xaxes(
    title_text="Date and Time",
    row=2,
    col=1
)

fig.update_yaxes(
    title_text="Index Level",
    row=1,
    col=1
)

fig.update_yaxes(
    title_text="Volume",
    row=2,
    col=1
)


# --------------------------------------------------
# SAVE CHART
# --------------------------------------------------

output_path = PLOTS_DIR / "raw_2022.html"

fig.write_html(output_path)

print(f"\nChart saved to: {output_path}")
print("Open the HTML file in your browser to explore the chart.")
