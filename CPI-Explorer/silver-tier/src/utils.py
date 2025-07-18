import panel as pn

__all__ = ['error_msg_handler']

def error_msg_handler(*args):
    if (errors := pn.state.cache.get("error_msg", [])):
        for msg in errors:
            pn.state.notifications.error(msg)
        pn.state.cache["error_msg"] = []
