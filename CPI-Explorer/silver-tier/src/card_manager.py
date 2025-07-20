from collections import defaultdict
import panel as pn

from .config import Settings

__all__ = ['create_layout','add_card']

cards = pn.state.cache['cards'] = {}
update_trigger = pn.state.cache['update_trigger'] = pn.widgets.Button(name='Update', button_type='primary', visible=False)


def add_card(content, tab, slot, need_update=False, need_clear=False, title="New Card",collapsed=False):
    
    new_card = pn.Card(
        content,
        title=title,
        collapsed=collapsed,           
    )    
    if need_clear:
        cards.clear()    
    cards[tab, slot]=new_card
    if need_update:
        update_trigger.clicks += 1


@pn.depends(update_trigger.param.clicks)
def create_layout(*args):
    """Create a layout containing all current cards, grouped into tabs."""
    if not pn.state.cache['cards'].keys():
        return
    
    tab_cards = defaultdict(list)
    sorted_keys = sorted(cards.keys(), key=lambda x: x[1])
    for (tab_index, _), card in ((key, cards[key]) for key in sorted_keys):
        tab_cards[tab_index].append(card)

    tab_0_cards = tab_cards[0]
    tab_1_cards = tab_cards[1]
    tab_2_cards = tab_cards[2]

    # Create new Tabs layout
    # new_tabs = pn.Tabs(
    #     ("CPI Data", pn.Column(*tab_0_cards)),
    #     ("Correlations", pn.Column(*tab_1_cards)),
    # )
    tab_list = []
    for tab_index in sorted(tab_cards.keys()):
        title = Settings.TAB_NAMES.get(tab_index, f"Tab {tab_index}")
        tab_list.append((title, pn.Column(*tab_cards[tab_index])))

    new_tabs = pn.Tabs(*tab_list)

    # Restore previously selected tab
    last_index = pn.state.cache.get("selected_tab_index", 0)
    new_tabs.active = last_index

    # Watch for tab change to persist selected tab index
    def update_selected_index(event):
        pn.state.cache["selected_tab_index"] = event.new

    new_tabs.param.watch(update_selected_index, "active")

    return new_tabs



# 41VI5A7R
