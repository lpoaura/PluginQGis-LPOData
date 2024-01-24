__copyright__ = "Copyright 2020-2021, Gispo Ltd"
__license__ = "GPL version 2"
__email__ = "info@gispo.fi"
__revision__ = "$Format:%H$"

from typing import Any, Callable

from .exceptions import QgsPluginException
from .i18n import tr
from .messages import MsgBar
from .tasks import FunctionTask


def log_if_fails(fn: Callable) -> Callable:
    """
    Use this as a decorator with functions and methods that
    might throw uncaught exceptions.
    """
    from functools import wraps

    @wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> None:  # noqa: ANN001
        try:
            # Qt injects False into some signals
            if args[1:] != (False,):
                fn(*args, **kwargs)
            else:
                fn(*args[:-1], **kwargs)
        except QgsPluginException as e:
            MsgBar.exception(e, **e.bar_msg, stack_info=True)
        except Exception as e:
            MsgBar.exception(tr("Unhandled exception occurred"), e, stack_info=True)

    return wrapper


def taskify(fn: Callable) -> Callable:
    """
    Decoration used to turn any function or method into a FunctionTask task.
    """
    from functools import wraps

    @wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> FunctionTask:  # noqa: ANN001
        return FunctionTask(lambda: fn(*args, **kwargs))

    return wrapper
