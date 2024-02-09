# Copyright © LFV

from hatchling.plugin import hookimpl
from reqstool_python_hatch_plugin.build_hook.hook import Decorator


@hookimpl
def hatch_register_build_hook():
    return Decorator
