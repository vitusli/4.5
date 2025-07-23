from . import (
    append,
    apply,
    auth,
    changelog,
    detail,
    download,
    favourite,
    hdri,
    navigate,
    options,
    path,
    reload,
)


def register():
    append.register()
    apply.register()
    auth.register()
    changelog.register()
    detail.register()
    download.register()
    favourite.register()
    hdri.register()
    navigate.register()
    options.register()
    path.register()
    reload.register()


def unregister():
    append.unregister()
    apply.unregister()
    auth.unregister()
    changelog.unregister()
    detail.unregister()
    download.unregister()
    favourite.unregister()
    hdri.unregister()
    navigate.unregister()
    options.unregister()
    path.unregister()
    reload.unregister()
