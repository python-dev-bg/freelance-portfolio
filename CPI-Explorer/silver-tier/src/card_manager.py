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
    """Create a layout containing all current cards."""
    print()
    return pn.Column(        
        *cards.values(),              
    )





