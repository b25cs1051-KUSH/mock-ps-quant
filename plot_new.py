import pandas as pd
import plotly.graph_objects as go

# ============================================================
# CONFIG
# ============================================================

FILE_PATH = "data/NIFTY_50_minute.csv"

SMA_PERIOD = 25
EMA_PERIOD = 25

SMA_SHORT_PERIOD = 9
EMA_SHORT_PERIOD = 20

SMA_20_PERIOD = 20
EMA_9_PERIOD = 9

LAST_N = 300


# ============================================================
# LOAD DATA
# ============================================================

if FILE_PATH.lower().endswith(".parquet"):
    df = pd.read_parquet(FILE_PATH)
else:
    df = pd.read_csv(FILE_PATH)


# ============================================================
# CLEAN DATA
# ============================================================

df.columns = df.columns.astype(str).str.strip()

df["date"] = pd.to_datetime(
    df["date"],
    dayfirst=True,
    errors="coerce"
)

df["close"] = pd.to_numeric(
    df["close"],
    errors="coerce"
)

df = df.dropna(
    subset=["date", "close"]
)

df = df.sort_values(
    "date"
).reset_index(drop=True)


# ============================================================
# CALCULATE INDICATORS
# ============================================================

# ------------------------------------------------------------
# SMA 25
# ------------------------------------------------------------

df["SMA_25"] = (
    df["close"]
    .rolling(
        window=SMA_PERIOD
    )
    .mean()
)


# ------------------------------------------------------------
# EMA 25
# ------------------------------------------------------------

df["EMA_25"] = (
    df["close"]
    .ewm(
        span=EMA_PERIOD,
        adjust=False
    )
    .mean()
)


# ------------------------------------------------------------
# SMA 9
# ------------------------------------------------------------

df["SMA_9"] = (
    df["close"]
    .rolling(
        window=SMA_SHORT_PERIOD
    )
    .mean()
)


# ------------------------------------------------------------
# EMA 20
# ------------------------------------------------------------

df["EMA_20"] = (
    df["close"]
    .ewm(
        span=EMA_SHORT_PERIOD,
        adjust=False
    )
    .mean()
)


# ------------------------------------------------------------
# SMA 20
# ------------------------------------------------------------

df["SMA_20"] = (
    df["close"]
    .rolling(
        window=SMA_20_PERIOD
    )
    .mean()
)


# ------------------------------------------------------------
# EMA 9
# ------------------------------------------------------------

df["EMA_9"] = (
    df["close"]
    .ewm(
        span=EMA_9_PERIOD,
        adjust=False
    )
    .mean()
)


# ============================================================
# TAKE LAST 300 DATA POINTS
# ============================================================

plot_df = df.tail(LAST_N).copy()


print("Total datapoints:", len(df))
print("Datapoints plotted:", len(plot_df))
print("From:", plot_df["date"].iloc[0])
print("To:", plot_df["date"].iloc[-1])


# ============================================================
# CREATE PLOT
# ============================================================

fig = go.Figure()


# ============================================================
# CLOSE PRICE
# ============================================================

fig.add_trace(
    go.Scatter(
        x=plot_df["date"],
        y=plot_df["close"],
        mode="lines",
        name="Close Price",
        line=dict(width=1.5)
    )
)


# ============================================================
# SMA 9
# ============================================================

fig.add_trace(
    go.Scatter(
        x=plot_df["date"],
        y=plot_df["SMA_9"],
        mode="lines",
        name="SMA 9",
        line=dict(width=2)
    )
)


# ============================================================
# EMA 9
# ============================================================

fig.add_trace(
    go.Scatter(
        x=plot_df["date"],
        y=plot_df["EMA_9"],
        mode="lines",
        name="EMA 9",
        line=dict(width=2)
    )
)


# ============================================================
# SMA 20
# ============================================================

fig.add_trace(
    go.Scatter(
        x=plot_df["date"],
        y=plot_df["SMA_20"],
        mode="lines",
        name="SMA 20",
        line=dict(width=2)
    )
)


# ============================================================
# EMA 20
# ============================================================

fig.add_trace(
    go.Scatter(
        x=plot_df["date"],
        y=plot_df["EMA_20"],
        mode="lines",
        name="EMA 20",
        line=dict(width=2)
    )
)


# ============================================================
# SMA 25
# ============================================================

fig.add_trace(
    go.Scatter(
        x=plot_df["date"],
        y=plot_df["SMA_25"],
        mode="lines",
        name="SMA 25",
        line=dict(width=2)
    )
)


# ============================================================
# EMA 25
# ============================================================

fig.add_trace(
    go.Scatter(
        x=plot_df["date"],
        y=plot_df["EMA_25"],
        mode="lines",
        name="EMA 25",
        line=dict(width=2)
    )
)


# ============================================================
# LAYOUT
# ============================================================

fig.update_layout(

    title=(
        f"Last {LAST_N} NIFTY 50 Minute Data"
        " - Close, SMA and EMA"
    ),

    xaxis_title="Date",

    yaxis_title="Price",

    template="plotly_white",

    hovermode="x unified",

    height=700,

    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1
    )
)


# ============================================================
# X-AXIS
# ============================================================

fig.update_xaxes(
    showgrid=True
)


# ============================================================
# Y-AXIS
# ============================================================

fig.update_yaxes(
    showgrid=True
)


# ============================================================
# DISPLAY
# ============================================================

fig.show()
