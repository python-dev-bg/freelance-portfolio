import datetime as dt
import polars as pl
import panel as pn
from .data_processor import *
from .widgets import *

__all__ = [
    'error_msg_handler','correlations_calculations','on_load_trigger','min_max_corr_handler',
    'type_corr_handler'
    ]

def on_load_trigger():     
    start, end = date_slider.value       
    new_end = end + dt.timedelta(days=1)
    new_end = end - dt.timedelta(days=1)
    date_slider.value = (start, new_end)
    benchmark_selector.value = [pn.state.cache["max_corr_bench_spearman"]]

def error_msg_handler(*args):
    if (errors := pn.state.cache.get("error_msg", [])):
        for msg in errors:
            pn.state.notifications.error(msg)
        pn.state.cache["error_msg"] = []


def correlations_calculations(event):
    print(f'correlations_calculations {event}')
    correlation_df = calc_correlations(event.new)
    pn.state.cache["correlation_df"]=correlation_df
    min_max_corr_df, filtered_corr_df = calc_min_max_correlations(
        correlation_df, country_selector.value, cpi_selector.value, change_mode.value)
    pn.state.cache[country_selector.value, ','.join(cpi_selector.value), change_mode.value, event.new] = min_max_corr_df, filtered_corr_df
    pn.state.cache["max_corr_bench_pearson"]=min_max_corr_df.filter(pl.col("correlation_type")=="Pearson").get_column("strongest_benchmark")[0]
    pn.state.cache["max_corr_bench_spearman"]=min_max_corr_df.filter(pl.col("correlation_type")=="Spearman").get_column("strongest_benchmark")[0]
    pn.state.cache["min_corr_bench_pearson"]=min_max_corr_df.filter(pl.col("correlation_type")=="Pearson").get_column("weakest_benchmark")[0]
    pn.state.cache["min_corr_bench_spearman"]=min_max_corr_df.filter(pl.col("correlation_type")=="Spearman").get_column("weakest_benchmark")[0]
    
    # pn.state.cache["selected_bench_by_coor"] = pn.state.cache["max_corr_bench_spearman"]

def min_max_corr_handler(event):
    if event.new and corr_type_selector.value == "Pearson":
        sel_bench = [pn.state.cache["max_corr_bench_pearson"]]
    elif event.new and corr_type_selector.value == "Spearman":
        sel_bench = [pn.state.cache["max_corr_bench_spearman"]]
    elif not event.new and corr_type_selector.value == "Pearson":
        sel_bench = [pn.state.cache["min_corr_bench_pearson"]]
    elif not event.new and corr_type_selector.value == "Spearman":
        sel_bench = [pn.state.cache["min_corr_bench_spearman"]]
    else:
        sel_bench = []
    benchmark_selector.value = sel_bench

def type_corr_handler(event):
    if event.new == "Pearson" and min_max_switch.value :
        sel_bench = [pn.state.cache["max_corr_bench_pearson"]]
    elif event.new == "Spearman" and min_max_switch.value:
        sel_bench = [pn.state.cache["max_corr_bench_spearman"]]
    elif event.new == "Pearson" and not min_max_switch.value:
        sel_bench = [pn.state.cache["min_corr_bench_pearson"]]
    elif event.new == "Spearman" and not min_max_switch.value:
        sel_bench = [pn.state.cache["min_corr_bench_spearman"]]
    else:
        sel_bench = []
    benchmark_selector.value = sel_bench