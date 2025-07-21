import panel as pn
import datetime as dt
from .config import Settings



__all__ = ['country_selector','cpi_selector','benchmark_selector','corr_type_selector',
           'date_slider','change_mode','export_btn','min_max_switch']

country_selector = pn.widgets.Select(
    name="Country",
    options=Settings.COUNTRIES,
    value=Settings.COUNTRIES[0]
)

cpi_selector = pn.widgets.CheckButtonGroup(
    name="CPI Types",
    options=Settings.CPI_CATEGORIES,
    value=[Settings.CPI_CATEGORIES[0]],
    button_style='outline',
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
    button_style='outline',
    
)

export_btn = pn.widgets.FileDownload(
    label="Download Filtered CSV",
    filename="filtered_cpi.csv",
    file=True,
    button_type="success"
)

min_max_switch = pn.widgets.Switch(name="Strongest / Weakest Correlation", value=True)

corr_type_selector = pn.widgets.Select(
    name="Corelation Types",
    options=["Pearson","Spearman"],
    # value=["Spearman"],
    # button_style='outline',
    # button_type="primary",
)