from . import lists, panels


def register():
    lists.register()
    panels.register()


def unregister():
    lists.unregister()
    panels.unregister()
