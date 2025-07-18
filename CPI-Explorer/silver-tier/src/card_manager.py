import panel as pn

__all__ = ['create_layout','add_card']

cards = pn.state.cache['cards'] = {}
update_trigger = pn.state.cache['update_trigger'] = pn.widgets.Button(name='Update', button_type='primary', visible=False)


def add_card(content, slot, need_update=False, need_clear=False, title="New Card",collapsed=False):
    
    new_card = pn.Card(
        content,
        title=title,
        collapsed=collapsed,           
    )    
    if need_clear:
        cards.clear()    
    cards[slot]=new_card
    if need_update:
        update_trigger.clicks += 1


@pn.depends(update_trigger.param.clicks)
def create_layout(*args):
    """Create a layout containing all current cards, grouped into tabs."""
    tab_1_cards = [card for key, card in cards.items() if "Correlation" not in card.title]
    tab_2_cards = [card for key, card in cards.items() if "Correlation" in card.title]
    # tab_1_cards = [card for key, card in cards.items() if key[0] == 0]
    # tab_2_cards = [card for key, card in cards.items() if key[0] == 1]
    # Create new Tabs layout
    new_tabs = pn.Tabs(
        ("CPI Data", pn.Column(*tab_1_cards)),
        ("Correlations", pn.Column(*tab_2_cards)),
    )

    # Restore previously selected tab
    last_index = pn.state.cache.get("selected_tab_index", 0)
    new_tabs.active = last_index

    # Watch for tab change to persist selected tab index
    def update_selected_index(event):
        pn.state.cache["selected_tab_index"] = event.new

    new_tabs.param.watch(update_selected_index, "active")

    return new_tabs




