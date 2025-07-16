import sys
from io import BytesIO
import polars as pl
import pandas as pd
from pathlib import Path
import panel as pn
import holoviews as hv
import logging
import hvplot.polars

pn.extension(
    'tabulator',
    design="material",
    sizing_mode='stretch_width',
    notifications=True,
    ready_notification='Application fully loaded.',
    
)
pn.config.throttled = True

logging.getLogger('root').setLevel(logging.ERROR)

DATA_FOLDER = 'data'
BASE_YEAR = 2015
FOOD_CATEGORIES = ["Food", "Total"]
BENCHMARK_CATEGORIES = ["Brent-Oil", "10-Year TY", "USD/EUR Spot", "Food Price Index", "ECB Food Commodity Index"]
HEIGHT = 700
CARD_WIDTH = 270
PLOT_COLORS = {
    ("Denmark", "Total"): "#78a3c5",        
    ("Denmark", "Food"): "#e6a96e",         
    ("Netherlands", "Total"): "#7fb27d",    
    ("Netherlands", "Food"): "#d1797a",     
    ("Global (Oil)", "Brent-Oil"): "#9b7b74",
    ("USA", "10-Year TY"):"#bee706" , 
    ("Global (USD/EUR)", "USD/EUR Spot"):"#f1bb1b",
    ("Global (FAO)", "Food Price Index"):"#30f11b",
    ("EU (ECB)", "ECB Food Commodity Index"): "#da489f",
}

# Get current working directory
cwd = Path.cwd()

# Get parent directory
parent_dir = cwd.parent

# Get data directory
data_dir = Path(parent_dir).joinpath(DATA_FOLDER)

# --- Load & Normalize Data ---
def load_series(file: str, country: str, category: str, need_adj: bool = False):    
    try:
        df = pl.read_csv(data_dir.joinpath(file))
        date_col = df.columns[0] if df.columns[0].lower() in {"date", "observation_date"} else "DATE"
    except FileNotFoundError as er:
        logging.error(er)
        sys.exit('Abort')
    df = (
        df.rename({df.columns[1]: "value"})
        .with_columns(
            pl.col(date_col).str.strptime(pl.Date, "%Y-%m-%d").alias("date"),
            pl.lit(country).alias("country"),
            pl.lit(category).alias("category")
        )
        .select(["date", "country", "category", "value"])
    )
    if need_adj:
        scale_factor = (
            100 / df.filter(pl.col("date").dt.year() == BASE_YEAR)
                    .get_column("value")
                    .median()
        )

        # 2. Apply scaling to all values
        df = df.with_columns(
            (pl.col("value") * scale_factor).round(1).alias("value")
        )
    return df

def load_fao_series(file: str, country: str, category: str, need_adj: bool = False) -> pl.DataFrame:
    try:
        pdf = pd.read_csv(data_dir.joinpath(file), header=2, usecols=range(7))
        df = pl.from_pandas(pdf).filter(pl.col("Date").is_not_null())
    except Exception as e:
        logging.error(f"Failed to load FAO data: {e}")
        sys.exit("Abort")
    a=10
    df = (
        df
        .rename({"Date": "date", "Food Price Index": "value"})
        .with_columns([
            pl.col("date").str.strptime(pl.Date, "%Y-%m"),
            pl.lit(country).alias("country"),
            pl.lit(category).alias("category")
        ])
        .select(["date", "country", "category", "value"])
    )
    if need_adj:
        scale = 100 / df.filter(pl.col("date").dt.year() == BASE_YEAR).get_column("value").median()
        df = df.with_columns((pl.col("value") * scale).round(1).alias("value"))
    return df

def load_ecb_food_commodity_index(file: str, country: str = "EU (ECB)", category: str = "ECB Food Commodity Index", need_adj: bool = False) -> pl.DataFrame:

    # ECB CSVs typically have metadata at the top; autodetect real header
    try:
        pdf = pd.read_csv(
            data_dir.joinpath(file),
            skiprows=0  # Adjust manually if metadata lines exist
        )
    except Exception as e:
        logging.error(f"Failed to load ECB data: {e}")
        sys.exit("Abort")

    # Rename & clean
    if 'TIME_PERIOD' not in pdf.columns or 'OBS_VALUE' not in pdf.columns:
        raise ValueError("Unexpected ECB format — expected 'TIME_PERIOD' and 'OBS_VALUE' columns")

    df = (
        pl.from_pandas(pdf[["TIME_PERIOD", "OBS_VALUE"]])
          .rename({"TIME_PERIOD": "date", "OBS_VALUE": "value"})
          .with_columns([
              pl.col("date").str.strptime(pl.Date, "%Y-%m"),
              pl.lit(country).alias("country"),
              pl.lit(category).alias("category"),
              pl.col("value").cast(pl.Float64)
          ])
          .select(["date", "country", "category", "value"])
          .filter(pl.col("value").is_not_null())
    )

    # Normalize to 2015 = 100
    if need_adj:
        base_median = (
            df.filter(pl.col("date").dt.year() == BASE_YEAR)
              .get_column("value").median()
        )
        df = df.with_columns(
            (pl.col("value") * (100 / base_median)).round(1).alias("value")
        )

    return df

df = pl.concat([
    load_series("CP0000DKM086NEST.csv", "Denmark", "Total"),
    load_series("CP0110DKM086NEST.csv", "Denmark", "Food"),
    load_series("CP0000NLM086NEST.csv", "Netherlands", "Total"),
    load_series("CP0110NLM086NEST.csv", "Netherlands", "Food"), 
    load_series("MCOILBRENTEU.csv", "Global (Oil)", "Brent-Oil", need_adj=True),  
    load_series("GS10.csv", "USA", "10-Year TY", need_adj=True),  
    load_series("EXUSEU.csv", "Global (USD/EUR)", "USD/EUR Spot", need_adj=True),  
    load_fao_series("food_price_indices_data_jul25.csv", "Global (FAO)", "Food Price Index", need_adj=True),
    load_ecb_food_commodity_index("STS_M_I9_N_ECPE_CFOOD0_3_000.csv")
])

# --- Prepare UI values ---

categories = df.select("category").unique().to_series().to_list()
min_date = df.filter(pl.col("country")=="Denmark").get_column("date").min()
max_date = df.filter(pl.col("country")=="Denmark").get_column("date").max()


# --- Widgets ---
country_selector = pn.widgets.MultiChoice(
    name="Country",
    options=["Denmark", "Netherlands"],
    value=["Denmark", "Netherlands"]
)

food_selector = pn.widgets.CheckBoxGroup(
    name="Food CPI Types",
    options=FOOD_CATEGORIES,
    value=FOOD_CATEGORIES
)

benchmark_selector = pn.widgets.CheckBoxGroup(
    name="Benchmarks",
    options=BENCHMARK_CATEGORIES,
    value=[]
)

date_slider = pn.widgets.DateRangeSlider(name="Date Range", start=min_date, end=max_date, value=(min_date, max_date))

change_mode = pn.widgets.RadioButtonGroup(
    name="Change Mode",
    options=["Index", "MoM %", "YoY %"],
    button_type="primary",
    value="Index",
    button_style='outline',
    
)

export_btn = pn.widgets.FileDownload(
    label="Download Filtered CSV",
    filename="filtered_cpi.csv",
    file=True,
    button_type="success"
)

def compute_kpis(df: pl.DataFrame, percent_mode: bool = False) -> pn.FlexBox:
    if df.is_empty():
        return pn.FlexBox(pn.pane.Markdown("⚠️ No data"))

    df = (
        df
        .with_columns(
            pl.col("date").max().over("category").alias('max_date')
        )        
    )
    common_latest_date = df.get_column("max_date").min()
    latest_df = df.filter(pl.col("date") == common_latest_date)
    cards = []
    available_categories = latest_df.select("category").unique().to_series()
    for country in sorted(latest_df.select("country").unique().to_series()):
        values = {}
        for category in available_categories:
            subset = latest_df.filter(
                (pl.col("country") == country) & (pl.col("category") == category)
            )
            if not subset.is_empty():
                val = subset.select("value")[0, 0]
                values[category] = val
                color = PLOT_COLORS.get((country, category), "#ddd")

                # Format based on % toggle
                if percent_mode:
                    display = f"{val:+.2%}"  
                else:
                    display = f"{val:.1f}" 

                cards.append(pn.pane.HTML(
                    f"""
                    <div style="background: {color}; border-radius: 6px; padding: 10px; text-align: center;">
                        <div style="font-size: 14px; font-weight: 600;">{country} – {category}</div>
                        <div style="font-size: 24px; font-weight: bold;">{display}</div>
                    </div>
                    """,
                    width=CARD_WIDTH, height=80
                ))

        # Add gap card if Food and Total both exist
        if "Food" in values and "Total" in values:
            diff = values["Food"] - values["Total"]
            gap_color = "#c8e6c9" if diff >= 0 else "#ffcdd2"
            gap_display = f"{diff:+.2%}" if percent_mode else f"{diff:+.2f}"
            cards.append(pn.pane.HTML(
                f"""
                <div style="background: {gap_color}; border-radius: 6px; padding: 10px; text-align: center;">
                    <div style="font-size: 14px; font-weight: 600;">{country} – Food vs Total</div>
                    <div style="font-size: 24px; font-weight: bold;">{gap_display}</div>
                </div>
                """,
                width=CARD_WIDTH, height=80
            ))

    cards.append(pn.pane.Markdown(f"📅 Latest: **{common_latest_date}**", width=200))
    return pn.FlexBox(*cards, sizing_mode="stretch_width", gap="10px")

# --- Callback Logic ---
@pn.depends(country_selector, food_selector, benchmark_selector, date_slider, change_mode)
def plot_cpi(country, food_cats, benchmark_cats, date_range, mode):
    # Build valid country-category combinations
    selected_pairs = [(c, cat) for c in country for cat in food_cats] + [
        (c, cat) for (c, cat) in PLOT_COLORS if cat in benchmark_cats
    ]

    # Now filter using tuple column logic
    raw_filtered = (
        df.with_columns(
            (pl.col("country") + "||" + pl.col("category")).alias("pair_key")
        )
        .filter(
            pl.col("pair_key").is_in([
                f"{c}||{cat}" for (c, cat) in selected_pairs
            ]) &
            (pl.col("date") >= date_range[0]) &
            (pl.col("date") <= date_range[1])
        )
        .drop("pair_key")
        .sort("date")
    )
    if raw_filtered.is_empty():
        return pn.pane.Markdown("### ⚠️ No data for current filter.")

    # Apply window-based % change if needed
    if mode == "MoM %":
        display_df = raw_filtered.with_columns(
            pl.col("value").pct_change().over(["country", "category"]).alias("value")
        )
        ylabel = "% change (MoM)"
    elif mode == "YoY %":
        display_df = raw_filtered.with_columns(
            (
                pl.col("value") / pl.col("value").shift(12) - 1
            ).over(["country", "category"]).alias("value")
        )
        ylabel = "% change (YoY)"
    else:
        display_df = raw_filtered
        ylabel = "Index (2015 = 100)"

    display_df = (
        display_df
        .with_columns(
            (pl.col("country") + " – " + pl.col("category")).alias("group_key")
        )        
    )
    color_map = {
        f"{country} – {category}": color
        for (country, category), color in PLOT_COLORS.items()
    }
   
    curves = []
    for key, group in display_df.to_pandas().groupby("group_key"):
        
        curve = hv.Curve(
            group,
            kdims=["date"],
            vdims=["value"],
            label=key
        ).opts(
            color=color_map.get(key, "gray"),
            tools=["hover"],
            line_width=2,            
            hover_tooltips=[
                ("Date", "@date{%F}"),
                ("Value", "@value{0.2f}"),
                ("Series", key)
            ],
            hover_formatters={"@date": "datetime"}
        )
        curves.append(curve)

    chart = hv.Overlay(curves).opts(
        height=HEIGHT,
        legend_position="bottom",
        show_legend=True,
        ylabel=ylabel,
        title="CPI Trend Over Time",
        responsive=True,
        show_grid=True
    )
    # Convert just for Tabulator (Panel doesn't support Polars in tables yet)
    table = pn.widgets.Tabulator(
        display_df.to_pandas(),
        pagination="remote", page_size=20, layout="fit_data_fill", height=int(HEIGHT/2)
    )
    pn.state.cache['data'] = display_df.clone()
    
    kpis = compute_kpis(display_df, percent_mode=(mode != "Index"))

    return pn.Column(kpis, chart, "### 📋 Filtered Data", table)


def download_callback():
    df_cached = pn.state.cache.get("data")
    if df_cached is None or df_cached.is_empty():
        return BytesIO(b"No data")
    
    # Create dynamic filename
    countries = "_".join(country_selector.value)
    date_range = f"{date_slider.value[0]}_to_{date_slider.value[1]}"
    suffix = {
        "Index": "idx",
        "MoM %": "mom",
        "YoY %": "yoy"
    }[change_mode.value]
    export_btn.filename = f"cpi_{countries}_{suffix}_{date_range}.csv"
    csv_bytes = df_cached.write_csv().encode("utf-8")
    buf = BytesIO(csv_bytes)
    buf.seek(0)
    return buf

export_btn.callback = download_callback

# --- Dashboard Layout ---
dashboard = pn.template.FastListTemplate(
    title="CPI Explorer Dashboard",    
    sidebar = pn.Column(
        pn.pane.Markdown("### Options", styles={"font-weight": "bold"}),
        pn.layout.Divider(),

        pn.pane.Markdown("#### Countries"),
        country_selector,

        pn.pane.Markdown("#### Food CPI"),
        food_selector,

        pn.layout.Divider(),

        pn.pane.Markdown("#### Benchmark indices"),
        benchmark_selector,

        pn.layout.Divider(),

        pn.pane.Markdown("#### Date Range"),
        date_slider,

        pn.layout.Divider(),

        pn.pane.Markdown("#### Change Mode"),
        pn.pane.Markdown("""\
    - **Index**: Raw values normalized to 2015 = 100  
    - **MoM %**: Month-over-Month % change  
    - **YoY %**: Year-over-Year % change
    """, styles={"font-size": "13px", "color": "#555"}),
        change_mode,

        pn.layout.Divider(),
        export_btn
    ),
    main=[plot_cpi]
)

dashboard.servable()