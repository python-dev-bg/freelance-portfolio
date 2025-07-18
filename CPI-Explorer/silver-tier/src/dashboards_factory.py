import panel as pn

from .widgets import *
from .card_manager import *

__all__ = ['create_dashboard','create_sidebar_1']

def create_sidebar_1():
    sidebar = pn.Column(
        pn.pane.Markdown("### Options", styles={"font-weight": "bold"}),
        pn.layout.Divider(),

        pn.pane.Markdown("#### Countries"),
        country_selector,

        pn.pane.Markdown("#### Food CPI"),
        cpi_selector,

        pn.layout.Divider(),

        pn.pane.Markdown("#### Benchmark indices"),
        benchmark_selector,

        pn.layout.Divider(),

        pn.pane.Markdown("#### Date Range"),
        date_slider,

        pn.layout.Divider(),

        pn.pane.Markdown("#### Change Mode"),
        pn.pane.Markdown("""\
    - **Index**: Raw values normalized to 2015 = 100  
    - **MoM %**: Month-over-Month % change  
    - **YoY %**: Year-over-Year % change
    """, styles={"font-size": "13px", "color": "#555"}),
        change_mode,

        pn.layout.Divider(),
        export_btn
    )
    return sidebar

def create_dashboard(sidebar_layout, main_layout, title, nav_bar_color='#bfc1c2'):
    # Create a layout that combines the main layout with the dynamic cards
    combined_main = [pn.Column(
        *main_layout,
        create_layout,
       
    )]
    
    dashboard = pn.template.FastListTemplate(
        busy_indicator=pn.indicators.LoadingSpinner(
            value=True, width=25, height=25, align="center", margin=(5, 0, 5, 10)
        ),
        theme_toggle=False,
        header_background=nav_bar_color,
        title=title,
        sidebar=sidebar_layout,
        main=combined_main
    )
    return dashboard