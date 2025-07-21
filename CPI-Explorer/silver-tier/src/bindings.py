import panel as pn
from .widgets import *
from .plotter import *
from .utils import *


date_slider.param.watch(correlations_calculations,'value')
corr_strength.param.watch(min_max_corr_handler, 'value')
corr_type_selector.param.watch(type_corr_handler, 'value')

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
    second_tab_plotter,
    country=country_selector,
    cpi=cpi_selector,
    benchmarks=benchmark_selector,
    date_range=date_slider,
    mode=change_mode,
    watch=True
)