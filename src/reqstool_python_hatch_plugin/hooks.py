# Copyright © LFV

from hatchling.plugin import hookimpl

from reqstool_python_hatch_plugin.build_hooks.reqstool import ReqstoolBuildHook


@hookimpl
def hatch_register_build_hook():
    return ReqstoolBuildHook
