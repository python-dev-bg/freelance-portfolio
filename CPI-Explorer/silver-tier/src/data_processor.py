import polars as pl
import panel as pn

from .config import Settings
from .widgets import *

__all__ = ['calc_correlations','compute_rolling_correlation','calc_min_max_correlations']

def calc_correlations(date_range: tuple):
    
    df = pn.state.cache["full_raw_data"]
    cpi_categories = Settings.CPI_CATEGORIES
    benchmarks = pn.state.cache["categories"]

    results = []

    for country in Settings.COUNTRIES:
        for cpi_cat in cpi_categories:
            for mode in ["Index", "MoM %", "YoY %"]:
                cpi_raw = (
                    df
                    .filter(
                        (pl.col("country") == country) & 
                        (pl.col("category") == cpi_cat)&
                        (pl.col("date") >= date_range[0]) &
                        (pl.col("date") <= date_range[1])
                    )
                    .sort("date")
                )
                if cpi_raw.is_empty():
                    continue

                if mode == "MoM %":
                    cpi_raw = cpi_raw.with_columns(
                        pl.col("value").pct_change().over(["country", "category"]).alias("value")
                    )
                elif mode == "YoY %":
                    cpi_raw = cpi_raw.with_columns(
                        (
                            pl.col("value") / pl.col("value").shift(12) - 1
                        ).over(["country", "category"]).alias("value")
                    )

                cpi_base = cpi_raw.select(["date", pl.col("value").alias("cpi_val")])
                cpi_ema3 = cpi_raw.with_columns(pl.col("value").ewm_mean(span=3).alias("cpi_ema3")).select(["date", "cpi_ema3"])
                cpi_ema6 = cpi_raw.with_columns(pl.col("value").ewm_mean(span=6).alias("cpi_ema6")).select(["date", "cpi_ema6"])

                for bench in benchmarks:
                    bench_raw = df.filter(pl.col("category") == bench).sort("date")
                    if bench_raw.is_empty():
                        continue

                    if mode == "MoM %":
                        bench_raw = bench_raw.with_columns(
                            pl.col("value").pct_change().over(["country", "category"]).alias("value")
                        )
                    elif mode == "YoY %":
                        bench_raw = bench_raw.with_columns(
                            (
                                pl.col("value") / pl.col("value").shift(12) - 1
                            ).over(["country", "category"]).alias("value")
                        )

                    bench_base = bench_raw.select(["date", pl.col("value").alias("bench_val")])
                    bench_ema3 = bench_raw.with_columns(pl.col("value").ewm_mean(span=3).alias("bench_ema3")).select(["date", "bench_ema3"])
                    bench_ema6 = bench_raw.with_columns(pl.col("value").ewm_mean(span=6).alias("bench_ema6")).select(["date", "bench_ema6"])

                    joined = (
                        cpi_base.join(bench_base, on="date", how="inner")
                        .join(cpi_ema3, on="date", how="inner")
                        .join(bench_ema3, on="date", how="inner")
                        .join(cpi_ema6, on="date", how="inner")
                        .join(bench_ema6, on="date", how="inner")
                        .drop_nulls()
                    )

                    if joined.height < 2:
                        continue

                    def corr(col1, col2):
                        return joined.select(pl.corr(col1, col2)).item()

                    def spearman(col1, col2):
                        ranked = joined.with_columns([
                            pl.col(col1).rank().alias("rank1"),
                            pl.col(col2).rank().alias("rank2")
                        ])
                        return ranked.select(pl.corr("rank1", "rank2")).item()

                    results.append({
                        "country": country,
                        "CPI": cpi_cat,
                        "benchmark": bench,
                        "mode": mode,
                        "Pearson": round(corr("cpi_val", "bench_val"), 3),
                        "Pearson (EMA3)": round(corr("cpi_ema3", "bench_ema3"), 3),
                        "Pearson (EMA6)": round(corr("cpi_ema6", "bench_ema6"), 3),
                        "Spearman": round(spearman("cpi_val", "bench_val"), 3),
                        "Spearman (EMA3)": round(spearman("cpi_ema3", "bench_ema3"), 3),
                        "Spearman (EMA6)": round(spearman("cpi_ema6", "bench_ema6"), 3)
                    })

    return pl.DataFrame(results)

def calc_min_max_correlations(correlation_df, country, cpi, mode):
    df = (
        correlation_df
        .filter((pl.col("country") == country) & (pl.col("CPI").is_in(cpi)) & (pl.col("mode") == mode))
        .unpivot(
            index=["CPI", "benchmark"],    
            on = ["Pearson", "Spearman"],     
            variable_name="correlation_type",
            value_name="correlation"
        )        
    )
    
    kpi_df = (
        df.with_columns([
            pl.col("correlation").abs().alias("abs_corr"),
            (pl.col("correlation").abs() - 0).abs().alias("dist_to_zero")
        ])
    )  

    strongest = (
        kpi_df.sort("abs_corr", descending=True)
            .group_by("correlation_type")
            .first()
            .select(["CPI", "correlation_type", "benchmark", "correlation"])
            .rename({"benchmark": "strongest_benchmark", "correlation": "strongest_value"})
    )

    weakest = (
        kpi_df.sort("dist_to_zero")
            .group_by("correlation_type")
            .first()
            .select(["CPI", "correlation_type", "benchmark", "correlation"])
            .rename({"benchmark": "weakest_benchmark", "correlation": "weakest_value"})
    )

    summary = (
        kpi_df
        .with_columns(
            (pl.col("abs_corr") > 0.7).cast(pl.Int64).alias("strong_corr_flag")
        )
        .group_by("correlation_type")
        .agg([
            pl.mean("abs_corr").alias("avg_abs_corr"),
            pl.sum("strong_corr_flag").alias("strong_corr_count")
        ])
    )

    final_kpi = strongest.join(weakest, on="correlation_type").join(summary, on="correlation_type")
    return final_kpi, df

def compute_rolling_correlation(df: pl.DataFrame, cpi: str, country: str, mode: str, benchmarks: list, window: int = 12):
    
    cpi_df = (
        df.filter(
            (pl.col("category").is_in(cpi)) & 
            (pl.col("country") == country)
        )
          .sort("date")
          .select(["date", "value"])
          .rename({"value": "cpi_value"})
    )

    if mode == "MoM %":
        cpi_df = cpi_df.with_columns(
            pl.col("cpi_value").pct_change().alias("cpi_value")
        )
    elif mode == "YoY %":
        cpi_df = cpi_df.with_columns(
            (pl.col("cpi_value") / pl.col("cpi_value").shift(12) - 1).alias("cpi_value")
        )

    results = []
    for benchmark in benchmarks:
        bdf = df.filter(pl.col("category") == benchmark).sort("date")
        bdf = bdf.select(["date", "value"]).rename({"value": "bench_val"})

        if mode == "MoM %":
            bdf = bdf.with_columns(pl.col("bench_val").pct_change().alias("bench_val"))
        elif mode == "YoY %":
            bdf = bdf.with_columns((pl.col("bench_val") / pl.col("bench_val").shift(12) - 1).alias("bench_val"))

        joined = (
            cpi_df.join(bdf, on="date", how="inner")
                  .drop_nulls()
        )
        if joined.height < window:
            continue

        rolling_corr = joined.select([
            pl.col("date"),
            pl.rolling_corr(pl.col("cpi_value"),pl.col("bench_val"), window_size=window).alias("rolling_corr")
        ]).with_columns([
            pl.lit(benchmark).alias("benchmark")
        ])

        results.append(rolling_corr)

    return pl.concat(results) if results else pl.DataFrame()

