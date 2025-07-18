import logging
from time import sleep
import panel as pn
import polars as pl
import pandas as pd
from pathlib import Path
from .config import Settings

logger = logging.getLogger("app_logger")

__all__ = []

def _data_preprocessor(df: pl.DataFrame, country: str, category: str):
    date_col = df.columns[0] if df.columns[0].lower() in {"date", "observation_date"} else "DATE"
    df = (
        df.rename({df.columns[1]: "value"})
        .with_columns(
            pl.col(date_col).str.strptime(pl.Date, "%Y-%m-%d").alias("date"),
            pl.lit(country).alias("country"),
            pl.lit(category).alias("category")
        )
        .select(["date", "country", "category", "value"])
    )
    return df


def _load_series(file: str, country: str, category: str, need_adj: bool = False):    
    try:
        df = pl.read_csv(Settings.DATA_FOLDER.joinpath(file))        
    except FileNotFoundError as e:
        logger.error(f"Failed to load {file} data: {e}")
        pn.state.cache["error_msg"].append(f"Failed to load {file} data: {e}")
    else:
        df = _data_preprocessor(df, country, category)
        if need_adj:
            scale_factor = (
                100 / df.filter(pl.col("date").dt.year() == Settings.BASE_YEAR)
                        .get_column("value")
                        .median()
            )
            # 2. Apply scaling to all values
            df = df.with_columns(
                (pl.col("value") * scale_factor).round(1).alias("value")
            )    
        pn.state.cache[category] = df

def _downloader(files_meta_dict):
    for series_name, f_name in files_meta_dict:        
        logger.debug("Start downloading {f_name} for {series_name}")
        try:
            df = pl.read_csv(f"{Settings.FRED_BASE_URL}{f_name}")
        except Exception as ex:
            logger.error(f"Error downloading {f_name} for {series_name}")
            pn.state.cache["error_msg"].append(f"Error downloading {f_name} for {series_name}")
            continue
        logger.debug(f"{f_name} for {series_name} downloaded successfully")
        country,category = series_name.split('_')
        df = _data_preprocessor(df, country, category)
        pn.state.cache[series_name] = df
        

def _load_fao_series(file: str, country: str, category: str, need_adj: bool = False) -> pl.DataFrame:
    try:
        pdf = pd.read_csv(Settings.DATA_FOLDER.joinpath(file), header=2, usecols=range(7))
        df = pl.from_pandas(pdf).filter(pl.col("Date").is_not_null())
    except Exception as e:
        logger.error(f"Failed to load FAO data: {e}")
        pn.state.cache["error_msg"].append(f"Failed to load FAO data: {e}")    
    else:    
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
            scale = 100 / df.filter(pl.col("date").dt.year() == Settings.BASE_YEAR).get_column("value").median()
            df = df.with_columns((pl.col("value") * scale).round(1).alias("value"))
        pn.state.cache[category] = df

def _load_ecb_food_commodity_index(file: str, country: str = "EU (ECB)", category: str = "ECB Food Commodity Index", need_adj: bool = False) -> pl.DataFrame:

    # ECB CSVs typically have metadata at the top; autodetect real header
    try:
        pdf = pd.read_csv(
            Settings.DATA_FOLDER.joinpath(file),
            skiprows=0  # Adjust manually if metadata lines exist
        )
    except Exception as e:
        logging.error(f"Failed to load ECB data: {e}")   
        pn.state.cache["error_msg"].append(f"Failed to load ECB data: {e}")      
    else:
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
                df.filter(pl.col("date").dt.year() == Settings.BASE_YEAR)
                .get_column("value").median()
            )
            df = df.with_columns(
                (pl.col("value") * (100 / base_median)).round(1).alias("value")
            )
        pn.state.cache[category] = df

def _data_merger():
    # data = [v for k,v in pn.state.cache.items() if k != "error_msg" and isinstance(v, pl.DataFrame)]
    data = []
    cats = []
    for cat, df in pn.state.cache.items():
        if cat != "error_msg" and isinstance(df, pl.DataFrame):
            data.append(df)
            cats.append(cat)

    try:
        merged_df = pl.concat(data)
        if merged_df.is_empty():
            raise ValueError("No input data !\nAbort !")
    except Exception as ex:
        logger.error(f"Error loading data!\n{ex} \nAbort !")
        pn.state.cache["error_msg"].append(f"Error loading data!\n{ex} \nAbort !")
    else:
        error_msg = pn.state.cache["error_msg"]
        pn.state.cache.clear()
        pn.state.cache["error_msg"] = error_msg
        pn.state.cache["merged_df"] = merged_df
        pn.state.cache["categories"] = sorted(set(Settings.BENCHMARK_CATEGORIES).intersection(set(cats)))
        dates = (
            merged_df
            .filter(pl.col("country").is_in(Settings.COUNTRIES))
            .with_columns(
                pl.col("date").min().over("country").alias("min_date"),
                pl.col("date").max().over("country").alias("max_date"),
            )
            .with_columns(
                pl.col("min_date").max().alias("max_min_date"),
                pl.col("max_date").min().alias("min_max_date"),
            )            
            .unique(["max_min_date","min_max_date"])
            .select("max_min_date","min_max_date")
        )
        pn.state.cache["min_date"] = dates["max_min_date"][0]
        pn.state.cache["max_date"] = dates["min_max_date"][0]

        

    

def load_initial_data():
    try:
        pn.state.cache.clear()
        pn.state.cache["error_msg"] = []
    except AttributeError:
        logger.error('Cache miss')    
    _downloader(Settings.CPI_FILES.items())
    _load_series(Settings.BRENT_FILE, "Global (Oil)", "Brent-Oil", need_adj=True)
    _load_series(Settings.TY10_FILE, "USA", "10-Year TY", need_adj=True)
    _load_series(Settings.USDEUR_SPOT_FILE, "Global (USD/EUR)", "USD/EUR Spot", need_adj=True)
    _load_fao_series(Settings.FAO_FOOD_FILE, "Global (FAO)", "Food Price Index", need_adj=True)
    _load_ecb_food_commodity_index(Settings.ECB_FODD_INDEX_FILE)
    _data_merger()
        
            
    

load_initial_data()