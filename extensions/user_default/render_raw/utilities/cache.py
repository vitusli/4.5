import bpy
from functools import lru_cache, wraps
from datetime import datetime, timedelta


def get_context(args):
    context_list=[x for x in args if isinstance(x, bpy.context.__class__)]
    return context_list[0] if context_list else None


def RR_cache(seconds: int, maxsize: int = None, animated=False):

    def wrapper_cache(func):
        func = lru_cache(maxsize=maxsize)(func)
        func.lifetime = timedelta(seconds=seconds)
        func.expiration = datetime.now() + func.lifetime
        func.frame = 0
        func.scene = None

        @wraps(func)
        def wrapped_func(*args, **kwargs):
            use_cache = bpy.context.scene.render_raw_scene.use_cache
            if(
                # True or # Uncomment True to see if a problem is cache related
                not use_cache or 
                ('use_cache' in kwargs and kwargs['use_cache'] == False) or
                datetime.now() >= func.expiration or 
                (bpy.context and bpy.context.scene != func.scene) or
                (animated and func.frame != bpy.context.scene.frame_current)
            ):
                func.cache_clear()
                func.expiration = datetime.now() + func.lifetime
                func.scene = bpy.context.scene
                if animated:
                    func.frame = bpy.context.scene.frame_current

            return func(*args, **kwargs)

        return wrapped_func

    return wrapper_cache


def cacheless(func):
    """ 
    Useful for making sure top level, non-drawing functions don't use cached data 
    """
    def wrapped(*args, **kwargs):
        RR_SCENE = bpy.context.scene.render_raw_scene
        was_enabled = RR_SCENE.use_cache

        # print('DISABLING CACHE')
        RR_SCENE.use_cache = False
        result = func(*args, **kwargs)
        RR_SCENE.use_cache = was_enabled
        # print(f'CHANGING CACHE: {was_enabled}')

        return result
        
    return wrapped
        
