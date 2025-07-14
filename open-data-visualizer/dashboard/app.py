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
HEIGHT = 700
PLOT_COLORS = {
    ("Denmark", "Total"): "#8fbbda",       
    ("Denmark", "Food"): "#ffbf87",        
    ("Netherlands", "Total"): "#95c895",   
    ("Netherlands", "Food"): "#eb9394",    
}

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

# def compute_kpis(df: pl.DataFrame) -> pn.Row:
#     if df.is_empty():
#         return pn.Row(pn.pane.Markdown("⚠️ No data for KPI display."))

#     latest_date = df.select("date").max()[0, 0]
#     latest_df = df.filter(pl.col("date") == latest_date)

#     cards = []
#     for country in country_selector.value:
#         values = {}
#         for category in category_selector.value:
#             subset = latest_df.filter(
#                 (pl.col("country") == country) &
#                 (pl.col("category") == category)
#             )
#             if not subset.is_empty():
#                 val = subset.select("value")[0, 0]
#                 values[category] = val
#                 color = PLOT_COLORS.get((country, category), "#888")
#                 cards.append(pn.indicators.Number(
#                     name=f"{country} - {category}",
#                     value=val,
#                     format="{value:.1f}",
#                     styles={"background": color, "padding": "8px", "borderRadius": "6px","alpha":"0.2"}
#                 ))
#         # Optional: compute Food vs Total gap
#         if "Food" in values and "Total" in values:
#             cards.append(pn.indicators.Number(
#                 name=f"{country} – Food vs Total",
#                 value=values["Food"] - values["Total"],
#                 format="{value:+.2f}"
#             ))

#     cards.append(pn.pane.Markdown(f"📅 Latest: **{latest_date}**", width=150))
#     return pn.FlexBox(*cards, sizing_mode="stretch_width", gap="10px")
def compute_kpis(df: pl.DataFrame, percent_mode: bool = False) -> pn.FlexBox:
    if df.is_empty():
        return pn.FlexBox(pn.pane.Markdown("⚠️ No data"))

    latest_date = df.select("date").max()[0, 0]
    latest_df = df.filter(pl.col("date") == latest_date)

    cards = []

    for country in country_selector.value:
        values = {}
        for category in category_selector.value:
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
                    width=200, height=80
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
                width=200, height=80
            ))

    cards.append(pn.pane.Markdown(f"📅 Latest: **{latest_date}**", width=200))
    return pn.FlexBox(*cards, sizing_mode="stretch_width", gap="10px")
# --- Callback Logic ---
@pn.depends(country_selector, category_selector, date_slider, percent_toggle)
def plot_cpi(countries, categories, date_range, pct):
    # Filter and sort
    raw_filtered = (
        df.filter(
            (pl.col("country").is_in(countries)) &
            (pl.col("category").is_in(categories)) &
            (pl.col("date") >= date_range[0]) &
            (pl.col("date") <= date_range[1])
        )
        .sort("date")
    )

    if raw_filtered.is_empty():
        return pn.pane.Markdown("### ⚠️ No data for current filter.")

    # Apply window-based % change if needed
    if pct:
        display_df = raw_filtered.with_columns(
            pl.col("value").pct_change().over(["country", "category"]).alias("value")
        )
        ylabel = "% change (MoM)"
    else:
        display_df = raw_filtered
        ylabel = "Index (2015 = 100)"

    
    chart = display_df.hvplot.line(
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
        display_df.to_pandas(),
        pagination="remote", page_size=20, layout="fit_data_fill", height=int(HEIGHT/2)
    )
    pn.state.cache['data'] = display_df.clone()
    
    kpis = compute_kpis(display_df if pct else raw_filtered, percent_mode=pct)

    return pn.Column(kpis, chart, "### 📋 Filtered Data", table)


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