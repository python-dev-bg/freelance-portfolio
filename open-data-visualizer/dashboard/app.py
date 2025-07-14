import sys
from io import BytesIO
import polars as pl
from pathlib import Path
import panel as pn
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
HEIGHT = 800
import os
print("Working dir:", os.getcwd())
# Get current working directory
cwd = Path.cwd()

# Get parent directory
parent_dir = cwd.parent

# Get data directory
data_dir = Path(parent_dir).joinpath(DATA_FOLDER)

# --- Load & Normalize Data ---
def load_series(file, country, category):    
    try:
        df = pl.read_csv(data_dir.joinpath(file))
        date_col = df.columns[0] if df.columns[0].lower() in {"date", "observation_date"} else "DATE"
    except FileNotFoundError as er:
        logging.error(er)
        sys.exit('Abort')
    return (
        df.rename({df.columns[1]: "value"})
          .with_columns([
              pl.col(date_col).str.strptime(pl.Date, "%Y-%m-%d").alias("date"),
              pl.lit(country).alias("country"),
              pl.lit(category).alias("category")
          ])
          .select(["date", "country", "category", "value"])
    )

df = pl.concat([
    load_series("CP0000DKM086NEST.csv", "Denmark", "Total"),
    load_series("CP0110DKM086NEST.csv", "Denmark", "Food"),
    load_series("CP0000NLM086NEST.csv", "Netherlands", "Total"),
    load_series("CP0110NLM086NEST.csv", "Netherlands", "Food"),
])

# --- Prepare UI values ---
countries = df.select("country").unique().to_series().to_list()
categories = df.select("category").unique().to_series().to_list()
min_date = df.select("date").min()[0, 0]
max_date = df.select("date").max()[0, 0]

# --- Widgets ---
country_selector = pn.widgets.MultiChoice(name="Country", options=countries, value=countries)
category_selector = pn.widgets.CheckBoxGroup(name="CPI Type", options=categories, value=categories)
date_slider = pn.widgets.DateRangeSlider(name="Date Range", start=min_date, end=max_date, value=(min_date, max_date))
percent_toggle = pn.widgets.Toggle(name="Show % change", value=False)
export_btn = pn.widgets.FileDownload(
    label="Download Filtered CSV",
    filename="filtered_cpi.csv",
    file=True,
    button_type="success"
)

# --- Callback Logic ---
@pn.depends(country_selector, category_selector, date_slider, percent_toggle)
def plot_cpi(countries, categories, date_range, pct):
    # Filter and sort
    filtered_df = (
        df.filter(
            (pl.col("country").is_in(countries)) &
            (pl.col("category").is_in(categories)) &
            (pl.col("date") >= date_range[0]) &
            (pl.col("date") <= date_range[1])
        )
        .sort("date")
    )

    if filtered_df.is_empty():
        return pn.pane.Markdown("### ⚠️ No data for current filter.")

    # Apply window-based % change if needed
    if pct:
        filtered_df = filtered_df.with_columns(
            pl.col("value").pct_change().over(["country", "category"]).alias("value")
        )
        ylabel = "% change (MoM)"
    else:
        ylabel = "Index (2015 = 100)"

    
    chart = filtered_df.hvplot.line(
        x="date", y="value", by=["country", "category"],
        title="CPI Trend Over Time", ylabel=ylabel,
        legend="bottom", responsive=True, height=HEIGHT, grid=True,
        hover_cols=[],  
        hover_tooltips=[
            ("Date", "@date{%F}"),
            ("Value", "@value{0.2f}"),
            ("Country", "@country"),
            ("Category", "@category")
        ]
    ).opts(
        tools=["hover"],
        hover_formatters={"@date": "datetime"},  
        legend_position="bottom"
    )
    # Convert just for Tabulator (Panel doesn't support Polars in tables yet)
    table = pn.widgets.Tabulator(
        filtered_df.to_pandas(),
        pagination="remote", page_size=20, layout="fit_data_fill", height=int(HEIGHT/2)
    )
    pn.state.cache['data'] = filtered_df.clone()
    
    return pn.Column(chart, "### 📋 filtered_df Data", table)


def download_callback():
    df_cached = pn.state.cache.get("data")
    if df_cached is None or df_cached.is_empty():
        return BytesIO(b"No data")
    
    # Create dynamic filename
    countries = "_".join(country_selector.value)
    date_range = f"{date_slider.value[0]}_to_{date_slider.value[1]}"
    suffix = "pct" if percent_toggle.value else "idx"
    export_btn.filename = f"cpi_{countries}_{suffix}_{date_range}.csv"
    csv_bytes = df_cached.write_csv().encode("utf-8")
    buf = BytesIO(csv_bytes)
    buf.seek(0)
    return buf

export_btn.callback = download_callback

# --- Dashboard Layout ---
dashboard = pn.template.FastListTemplate(
    title="CPI Explorer Dashboard",
    sidebar=[country_selector, category_selector, date_slider, percent_toggle, export_btn],
    main=[plot_cpi]
)

dashboard.servable()