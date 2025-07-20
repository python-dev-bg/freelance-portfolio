import panel as pn
from .widgets import *
from .plotter import *
from .utils import *

# Bind the CPI plot handler
cpi_hndl = pn.bind(
    first_tab_plotter,
    country=country_selector,
    cpi=cpi_selector,
    benchmarks=benchmark_selector,
    date_range=date_slider,
    mode=change_mode,
    watch=True
)

# Bind the correlation matrix plot handler
coor_hndl = pn.bind(
    first_tab_plotter,
    country=country_selector,
    cpi=cpi_selector,
    benchmarks=benchmark_selector,
    date_range=date_slider,
    mode=change_mode,
    watch=True
)