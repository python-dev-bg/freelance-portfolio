import polars as pl
import panel as pn

from .config import Settings

__all__ = ['calc_correlations']


def calc_correlations(date_range: tuple):
    df = pn.state.cache["merged_df"]
    cpi_categories = Settings.CPI_CATEGORIES
    benchmarks = pn.state.cache["categories"]
    
    results = []

    for country in Settings.COUNTRIES:
        for cpi_cat in cpi_categories:
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

            cpi_base = cpi_raw.select(["date", pl.col("value").alias("cpi_val")])
            cpi_ema3 = cpi_raw.with_columns(pl.col("value").ewm_mean(span=3).alias("cpi_ema3")).select(["date", "cpi_ema3"])
            cpi_ema6 = cpi_raw.with_columns(pl.col("value").ewm_mean(span=6).alias("cpi_ema6")).select(["date", "cpi_ema6"])

            for bench in benchmarks:
                bench_raw = df.filter(pl.col("category") == bench).sort("date")
                if bench_raw.is_empty():
                    continue

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
                    "Pearson": round(corr("cpi_val", "bench_val"), 3),
                    "Pearson (EMA3)": round(corr("cpi_ema3", "bench_ema3"), 3),
                    "Pearson (EMA6)": round(corr("cpi_ema6", "bench_ema6"), 3),
                    "Spearman": round(spearman("cpi_val", "bench_val"), 3),
                    "Spearman (EMA3)": round(spearman("cpi_ema3", "bench_ema3"), 3),
                    "Spearman (EMA6)": round(spearman("cpi_ema6", "bench_ema6"), 3)
                })

    # pn.state.cache["correlation_df"] = pl.DataFrame(results)
    return  pl.DataFrame(results)
     

