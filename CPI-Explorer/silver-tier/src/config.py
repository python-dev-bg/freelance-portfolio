from pathlib import Path

__all__ = ["Settings"]

class Settings:
    ENV = "dev"
    DATA_FOLDER = Path(Path.cwd().parent).joinpath("data")
    BASE_YEAR = 2015
    CPI_CATEGORIES = ["Food", "Total"]
    BENCHMARK_CATEGORIES = ["Brent-Oil", "10-Year TY", "USD/EUR Spot", "Food Price Index", "ECB Food Commodity Index"]
    COUNTRIES = ["Denmark", "Netherlands"]
    MODES = ["Index", "MoM %", "YoY %"]
    HEIGHT = 500
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
    CPI_FILES = {
        "Denmark_Total":"CP0000DKM086NEST",
        "Netherlands_Total":"CP0000NLM086NEST",
        "Denmark_Food":"CP0110DKM086NEST",
        "Netherlands_Food":"CP0110NLM086NEST",
    }
    FRED_BASE_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id="
    BRENT_FILE = "MCOILBRENTEU.csv"
    TY10_FILE = "GS10.csv"
    USDEUR_SPOT_FILE = "EXUSEU.csv"
    FAO_FOOD_FILE = "food_price_indices_data_jul25.csv"
    ECB_FODD_INDEX_FILE = "STS_M_I9_N_ECPE_CFOOD0_3_000.csv"
    PEARSON_COL="#ff7f0e"
    SPEARMAN_COL="#1f77b4"
