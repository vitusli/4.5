from . import auth, icon, prefs, product, props
from .addon import *
from .auth import *
from .icon import *


def register():
    auth.register()
    icon.register()
    prefs.register()
    props.register()
    product.register()


def unregister():
    auth.unregister()
    icon.unregister()
    prefs.unregister()
    props.unregister()
    product.unregister()
