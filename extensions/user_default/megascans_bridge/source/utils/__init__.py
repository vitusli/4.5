from . import icon, manual, prefs, preview, props


def register():
    icon.register()
    manual.register()
    preview.register()
    props.register()
    prefs.register()


def unregister():
    icon.unregister()
    manual.unregister()
    preview.unregister()
    props.unregister()
    prefs.unregister()
