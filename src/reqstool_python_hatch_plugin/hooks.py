# Copyright © LFV

from hatchling.plugin import hookimpl

from reqstool_python_hatch_plugin.build_hooks.reqstool_decorators import ReqstoolDecorators


@hookimpl
def hatch_register_build_hook():
    return ReqstoolDecorators
