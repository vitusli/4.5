from . import (
    asset,
    atlas,
    brush,
    decal,
    detail,
    displacement,
    imperfection,
    navigate,
    options,
    plant,
    surface,
)


def register():
    asset.register()
    atlas.register()
    brush.register()
    decal.register()
    displacement.register()
    detail.register()
    imperfection.register()
    navigate.register()
    options.register()
    plant.register()
    surface.register()


def unregister():
    asset.unregister()
    atlas.unregister()
    brush.unregister()
    decal.unregister()
    displacement.unregister()
    detail.unregister()
    imperfection.unregister()
    navigate.unregister()
    options.unregister()
    plant.unregister()
    surface.unregister()
