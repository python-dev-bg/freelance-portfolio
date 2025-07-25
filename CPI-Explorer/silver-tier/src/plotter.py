import polars as pl
import panel as pn
import holoviews as hv

import hvplot.polars

from .config import Settings
from .card_manager import *
from .data_processor import *
from .widgets import *

__all__ = ["first_tab_plotter","second_tab_plotter"]

def first_tab_plotter(
        country,
        cpi,
        benchmarks,
        date_range,
        mode,
        
    ):
    if not benchmarks and not pn.state.cache["cards"]:       
        return
    
    correlation_df = pn.state.cache["full_correlations_data"]
    # slot 0
    cpi_plot = plot_cpi(country, cpi, benchmarks, date_range, mode)
    add_card(content=cpi_plot, tab=0, slot=0, title=f"CPI Data {country}")
    # slot 1
    heat_plots = plot_correlation_heatmaps(correlation_df, country, cpi, mode)
    add_card(heat_plots, tab=0, slot=1, need_update=True, need_clear=False, title=f"Correlations for {country} in mode {mode}")

def second_tab_plotter(
        country,
        cpi,
        benchmarks,
        date_range,
        mode,
    ):
    if not benchmarks and not pn.state.cache["cards"]:        
        return
    correlation_df = pn.state.cache["full_correlations_data"]
    ema_corr_plots = plot_correlation_matrix(correlation_df, country, cpi, benchmarks, date_range, mode)
    add_card(content=ema_corr_plots, tab=1, slot=0, need_update=False, need_clear=False, title=f"EMA correlation matrix for {country}")
    rolling_corr_plt = plot_rolling_correlation(country, cpi, mode, date_range, benchmarks, window = 12)
    add_card(content=rolling_corr_plt, tab=1, slot=1, need_update=True, need_clear=False, title=f"Rolling correlations Data {country}")
    

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

def plot_cpi(country, cpi, benchmarks, date_range, mode):
    # Build valid country-category combinations
    
    selected_pairs = [(country, cat)  for cat in cpi] + [
        (country, cat) for (country, cat) in Settings.PLOT_COLORS if cat in benchmarks
    ]
    df = pn.state.cache["full_raw_data"]
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
   
    return pn.Column(kpis, chart)

def plot_correlation_heatmaps(correlation_df, country, cpi, mode):   
    try:
        min_max_corr_df, filtered_corr_df = pn.state.cache[country, ','.join(cpi_selector.value), mode, date_slider.value]
    except KeyError:
        min_max_corr_df, filtered_corr_df = calc_min_max_correlations(correlation_df, country, cpi, mode)
    plots = []
    for corr_type in ["Pearson", "Spearman"]:
        plot_df = (
            filtered_corr_df
            .filter(pl.col("correlation_type") == corr_type)           
        ) 
        heatmap = plot_df.hvplot.heatmap(
            x="benchmark",
            y="CPI",
            C="correlation",
            cmap="seismic",
            clim=(-1, 1),
            colorbar=True,
            title=f"{corr_type} Correlations ({mode})",
            height=Settings.HEIGHT,
            responsive=True,
            rot=45

        )
        plots.append(heatmap)

    if "CPI_right" in min_max_corr_df.columns:
        final_kpi_df = (
            min_max_corr_df
            .rename({"CPI":"CPI_strongest", "CPI_right":"CPI_weakest"})
        )
    return pn.Column(
        pn.pane.DataFrame(final_kpi_df.to_pandas(), height=140),
        pn.Row(*plots)
    )  


def plot_rolling_correlation(country: str, cpi: str, mode: str, date_range: tuple, benchmarks: list, window: int = 12):
    df = pn.state.cache["full_raw_data"]
    
    if not benchmarks:
        return pn.pane.Markdown("### ⚠️ No data for current filter.")
    benchmark_colors = {
        bench: color for (country, bench), color in Settings.PLOT_COLORS.items()
    }
    df = df.filter((pl.col("date") >= date_range[0]) & (pl.col("date") <= date_range[1]))
    r_df = compute_rolling_correlation(df, cpi, country, mode, benchmarks, window)

    if r_df.is_empty():
        return pn.pane.Markdown("### ⚠️ Not enough data for rolling correlation")
    r_df = (
        r_df
        .with_columns(
            pl.col('benchmark').replace(benchmark_colors).alias('col')
        )
    )
    return r_df.hvplot.line(
        x="date", y="rolling_corr", by="benchmark",
        color="col",
        title=f"Rolling Pearson Correlation ({cpi}({mode}) of {country} with {benchmarks})",
        xlabel="Date", ylabel="Correlation",
        grid=True, responsive=True, height=Settings.HEIGHT
    )


def plot_correlation_matrix(correlation_df, country: str, cpi: list, benchmarks: list, date_range: tuple, mode: str):
    correlation_order = [
        "Pearson", "Spearman",
        "Pearson (EMA3)", "Spearman (EMA3)",
        "Pearson (EMA6)", "Spearman (EMA6)"
    ]
    benchmarks =  pn.state.cache["categories"]

    df_long = (
        correlation_df
        .filter(
            (pl.col("country")==country) &
            (pl.col("CPI").is_in(cpi)) &
            (pl.col("benchmark").is_in(benchmarks)) &
            (pl.col("mode") == mode  )      
        )
        .unpivot(
            index=["country", "CPI", "benchmark","mode"],            
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
        .sort(["correlation_type","benchmark","correlation"],descending=True)
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
    return plot
