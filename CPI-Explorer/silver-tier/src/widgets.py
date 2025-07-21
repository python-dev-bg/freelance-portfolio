from io import BytesIO
import panel as pn
from .config import Settings



__all__ = ["country_selector","cpi_selector","benchmark_selector","corr_type_selector","file_download",
           "date_slider","change_mode","download_click_bth","corr_strength","download_selector"]

country_selector = pn.widgets.Select(
    name="Country",
    options=Settings.COUNTRIES,
    value=Settings.COUNTRIES[0]
)

cpi_selector = pn.widgets.CheckButtonGroup(
    name="CPI Types",
    options=Settings.CPI_CATEGORIES,
    value=[Settings.CPI_CATEGORIES[0]],
    button_style="outline",
    button_type="primary",
)


benchmark_selector = pn.widgets.MultiChoice(
    name="Benchmarks",
    options=pn.state.cache["categories"],
    value=[],
    placeholder="May select one or more benchmarks..."
)

date_slider = pn.widgets.DateRangeSlider(
    name="Date Range", 
    start = pn.state.cache["min_date"], 
    end= pn.state.cache["max_date"], 
    value=(pn.state.cache["min_date"], pn.state.cache["max_date"])
)

change_mode = pn.widgets.RadioButtonGroup(
    name="Change Mode",
    options=Settings.MODES,
    button_type="primary",
    value="Index",
    button_style="outline",
    
)


corr_type_selector = pn.widgets.RadioButtonGroup(
    name="Corelation Types",
    options=["Pearson","Spearman"],
    button_type="primary",
    value="Spearman",
    button_style="outline",
)

corr_strength = pn.widgets.RadioButtonGroup(
    name="Strength Mode",
    options=["Weakest","Strongest"],
    button_type="primary",
    value="Strongest",
    button_style="outline",    
)

download_selector = pn.widgets.Select(
    name="Files",
    options=Settings.DOWNLOADS_FILES,    
)

download_click_bth = pn.widgets.Button(
    name="Download",    
    button_type="success"
)

file_download = pn.widgets.FileDownload(
    auto=True,
    label="Download as CSV", 
    filename="placeholder.csv",
    callback=lambda: BytesIO(b""),
    button_type="success",
    visible=True
)