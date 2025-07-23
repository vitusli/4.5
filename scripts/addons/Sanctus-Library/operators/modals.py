
from .. import auto_load as al
from ..auto_load.common import *

_IS_GIZMO_RUNNING = False
GIZMO_RUNNING_ASSERT = al.OperatorAssert(lambda: not _IS_GIZMO_RUNNING, 'Gizmo operation already running.')

def SET_GIZMO_RUNNING(value: bool):
    global _IS_GIZMO_RUNNING
    _IS_GIZMO_RUNNING = value

class ModalHelper:

    VIEW_DRAW_HANDLE_ATTR = '_draw_handle_view'

    @staticmethod
    def is_event_cancel(event: bt.Event):
        return event.type == al.BEventType.ESC() and event.value == al.BEventValue.PRESS()

    @staticmethod
    def is_event_confirm(event: bt.Event):
        return event.type == al.BEventType.LEFTMOUSE() and event.value == al.BEventValue.PRESS()
    
    @staticmethod
    def get_event_scroll(event: bt.Event):
        if not event.type in (al.BEventType.WHEELUPMOUSE(), al.BEventType.WHEELDOWNMOUSE()):
            return 0
        return 1 if event.type == al.BEventType.WHEELUPMOUSE() else -1
    
    @staticmethod
    def is_event_shift_release(event: bt.Event):
        return event.type in (al.BEventType.LEFT_SHIFT(), al.BEventType.RIGHT_SHIFT()) and event.value == al.BEventValue.RELEASE()
    
    @staticmethod
    def is_event_shift_pressed(event: bt.Event):
        if event.alt: return False
        if event.ctrl: return False
        return event.shift
    
    @staticmethod
    def is_event_alt_pressed(event: bt.Event):
        if event.shift: return False
        if event.ctrl: return False
        return event.alt
    
    @staticmethod
    def is_event_ctrl_pressed(event: bt.Event):
        if event.shift: return False
        if event.alt: return False
        return event.ctrl

    @classmethod
    def add_draw_handler_view(cls, operator: bt.Operator, callback: typing.Callable, args: tuple, region: str = 'WINDOW', draw_type: str = 'POST_PIXEL'):
        h = bt.SpaceView3D.draw_handler_add(callback, args, region, draw_type)
        setattr(operator, cls.VIEW_DRAW_HANDLE_ATTR, h)

    @classmethod
    def remove_draw_handler_view(cls, operator: bt.Operator, region: str = 'WINDOW'):
        handle = getattr(operator, cls.VIEW_DRAW_HANDLE_ATTR, None)
        if handle is not None:
            bt.SpaceView3D.draw_handler_remove(handle, region)
