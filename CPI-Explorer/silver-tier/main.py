import sys
import logging

import panel as pn
pn.extension(    
    design="material",
    sizing_mode='stretch_width',
    notifications=True,
    ready_notification='Application fully loaded.',
)
pn.config.throttled = True
pn.state.notifications.position = "bottom-right"

error_box = pn.pane.Alert("", alert_type="danger", visible=False)
from src import *

logger = logging.getLogger("app_logger")

def main(port):      
    
    tab1 = first_tab_plotter(
        country_selector.value,
        cpi_selector.value, 
        benchmark_selector.value, 
        date_slider.value, 
        change_mode.value,
    )
    # tab2 = plot_correlation_matrix(
    #     country_selector.value, 
    #     cpi_selector.value, 
    #     benchmark_selector.value, 
    #     date_slider.value,
    #     change_mode.value
    # )
    # tab2 = plot_correlation_heatmaps(
    #     country_selector.value, 
        
    #     date_slider.value,
    #     change_mode.value
    # )
    tab2 = first_tab_plotter(
        country_selector.value,
        cpi_selector.value, 
        benchmark_selector.value, 
        date_slider.value, 
        change_mode.value,
    )

    tabs = pn.Tabs(
        ("CPI", tab1),
        ("Correlations", tab2)
    )

    dashboard = create_dashboard(
        sidebar_layout=create_sidebar_1(),
        main_layout=[],
        title='Silver'
    )

    pn.serve(        
        panels={
            '1.Evaluation': dashboard,            
        },
        port=port,
        autoreload=False,
        show=True
    )    

if __name__ == '__main__':
    port = int(sys.argv[2]) if len(sys.argv) > 1 else 5007
    main(port)
