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

from src import *

logger = logging.getLogger("app_logger")

def main(port):      

    dashboard = create_dashboard(
        sidebar_layout=create_sidebar(),
        main_layout=[],
        title='CPI Explorer Dashboard Silver Tier'
    )  

    pn.state.onload(on_load_trigger)      

    pn.serve(        
        dashboard,
        port=port,
        autoreload=False,
        show=True
    )    

if __name__ == '__main__':
    port = int(sys.argv[2]) if len(sys.argv) > 1 else Settings.PORT
    main(port)

