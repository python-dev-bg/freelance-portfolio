import panel as pn
from .widgets import *
from .plotter import *
from .utils import *

cpi_hndl= pn.bind(plot_cpi, country_selector, cpi_selector, benchmark_selector, date_slider, change_mode,watch=True)
coor_hndl= pn.bind(plot_correlation_matrix, country_selector, cpi_selector, benchmark_selector, date_slider, watch=True)




