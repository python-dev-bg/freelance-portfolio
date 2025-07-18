import polars as pl
import panel as pn
import holoviews as hv
import hvplot.polars

from .config import Settings
from .card_manager import *
from .data_processor import *

__all__ = ["plot_correlation_matrix","plot_cpi"]


def plot_correlation_matrix(country: str, cpi: list, benchmarks: list, date_range: tuple):
    correlation_order = [
        "Pearson", "Spearman",
        "Pearson (EMA3)", "Spearman (EMA3)",
        "Pearson (EMA6)", "Spearman (EMA6)"
    ]
    benchmarks = benchmarks or pn.state.cache["categories"]
    correlation_df = calc_correlations(date_range)
    df_long = (
        correlation_df
        .filter(
            (pl.col("country")==country) &
            (pl.col("CPI").is_in(cpi)) &
            (pl.col("benchmark").is_in(benchmarks))        
        )
        .unpivot(
            index=["country", "CPI", "benchmark"],            
            variable_name="correlation_type",
            value_name="correlation"
        )
        .with_columns([
            (pl.col("benchmark") + " — " + pl.col("country") + ", " + pl.col("CPI")).alias("label"),
            pl.when(pl.col("correlation_type").is_in(correlation_order))
            .then(pl.col("correlation_type").cast(pl.Enum(correlation_order)))
            .alias("correlation_type"),
            pl.col("correlation_type").map_elements(
                lambda x: Settings.PEARSON_COL if str(x).startswith("Pearson") else Settings.SPEARMAN_COL,
                return_dtype=pl.String
            ).alias("color")
        ])
        .sort(["correlation_type","benchmark"],descending=True)
    )

    plot = df_long.hvplot.bar(
        x="label",
        y="correlation",
        by="correlation_type",
        title="correlation of CPI with Benchmarks (Pearson vs Spearman)",
        ylabel="correlation",
        xlabel="benchmark, country, CPI",
        height=Settings.HEIGHT,
        responsive=True,
        rot=45,
        grid=True,
        legend="top_right",
        color="color"
    )
    add_card(plot, slot=1, need_update=True, need_clear=False, title=f"Correlations for {country}")
    
def plot_correlation_matrix_(country: str, cpi: list, benchmarks: list):
    benchmarks = benchmarks or pn.state.cache["categories"]
    correlation_df = calc_correlations()

    df_long = (
        correlation_df
        .filter(
            (pl.col("country") == country) &
            (pl.col("CPI").is_in(cpi)) &
            (pl.col("benchmark").is_in(benchmarks))
        )
        .unpivot(
            index=["country", "CPI", "benchmark"],
            variable_name="correlation_type",
            value_name="correlation"
        )
        .with_columns([
            (pl.col("benchmark") + " — " + pl.col("country") + ", " + pl.col("CPI")).alias("label")
        ])
    )

    # color map
    color_map = {
        "Pearson": "#1f77b4",
        "Pearson (EMA3)": "#2ca02c",
        "Pearson (EMA6)": "#17becf",
        "Spearman": "#ff7f0e",
        "Spearman (EMA3)": "#d62728",
        "Spearman (EMA6)": "#9467bd",
    }

    overlays = []
    for corr_type in df_long["correlation_type"].unique().to_list():
        if corr_type not in color_map:
            continue

        df_sub = df_long.filter(pl.col("correlation_type") == corr_type)

        plot = df_sub.hvplot.bar(
            x="label",
            y="correlation",
            color=color_map[corr_type],
            legend_label=corr_type,
            height=Settings.HEIGHT
        )
        overlays.append(plot)

    final_plot = hv.Overlay(overlays).opts(
        title=f"correlation of CPI with Benchmarks (Pearson vs Spearman)",
        xlabel="benchmark, country, CPI",
        ylabel="correlation",
        show_grid=True,
        xrotation=45,
        legend_position="top_right",
        responsive=True
    )

    add_card(final_plot, slot=1, need_update=True, need_clear=False, title=f"Correlations for {country}")

def _compute_kpis(df: pl.DataFrame, percent_mode: bool = False) -> pn.FlexBox:
    if df.is_empty():
        return pn.FlexBox(pn.pane.Markdown("⚠️ No data"))

    df = (
        df
        .with_columns(
            pl.col("date").max().over("category").alias("max_date")
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
                color = Settings.PLOT_COLORS.get((country, category), "#ddd")

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
                    width=Settings.CARD_WIDTH, height=80
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
                width=Settings.CARD_WIDTH, height=80
            ))

    cards.append(pn.pane.Markdown(f"📅 Latest: **{common_latest_date}**", width=200))
    return pn.FlexBox(*cards, sizing_mode="stretch_width", gap="10px")


def plot_cpi(country, food_cats, benchmark_cats, date_range, mode):
    # Build valid country-category combinations
    
    selected_pairs = [(country, cat)  for cat in food_cats] + [
        (country, cat) for (country, cat) in Settings.PLOT_COLORS if cat in benchmark_cats
    ]
    df = pn.state.cache["merged_df"]
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
        for (country, category), color in Settings.PLOT_COLORS.items()
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
        height=Settings.HEIGHT,
        legend_position="bottom",
        show_legend=True,
        ylabel=ylabel,
        title="CPI Trend Over Time",
        responsive=True,
        show_grid=True
    )       
    kpis = _compute_kpis(display_df, percent_mode=(mode != "Index"))
    add_card(pn.Column(kpis, chart),slot=0, need_update=True, need_clear=False, title=f"CPI Data")