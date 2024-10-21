# Copyright © LFV

from hatchling.builders.hooks.plugin.interface import BuildHookInterface
from reqstool_python_decorators.processors.decorator_processor import DecoratorProcessor


class ReqstoolDecorators(BuildHookInterface):
    """
    Build hook that creates reqstool annotations files based on reqstool decorators.
    Attributes:
        PLUGIN_NAME (str): The name of the plugin, set to "reqstool_decorators".

    Methods:
        initialize(version, build_data):
            Executes custom actions during the build process, such as processing decorated Python files.
    """

    PLUGIN_NAME = "reqstool_decorators"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__config_path = None

    def initialize(self, version, build_data):
        path = self.config.get("path", [])

        decorator_processor = DecoratorProcessor()
        decorator_processor.process_decorated_data(path_to_python_files=path)
