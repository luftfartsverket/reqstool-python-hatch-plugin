# Copyright © LFV


from hatchling.builders.hooks.plugin.interface import BuildHookInterface
from reqstool_python_decorators.processors.decorator_processor import ProcessDecorator


class Decorator(BuildHookInterface):
    """
    A class that contains code that will run during the Hatch build process.

    Attributes:
    - `PLUGIN_NAME` (str): The name of the plugin.
    - `__config_path` (list): The path configuration for the decorator.

    Methods:
    - `get_config_path` : Get the configuration path.
    - `initialize` : contains the code that will be run during the Hatch build process.
    """

    PLUGIN_NAME = "decorators"

    def __init__(self, *args, **kwargs):
        """
        Initialize the Decorator instance.

        Args:
        - *args: Additional arguments.
        - **kwargs: Additional keyword arguments.
        """
        super().__init__(*args, **kwargs)
        self.__config_path = None

    @property
    def get_config_path(self):
        """
        Get the configuration path from the pyproject.toml file of the project using this plugin.

        Returns:
        - `list`: Path(s) from the configuration.
        """
        if self.__config_path is None:
            path = self.config.get("path", [])

            self.__config_path = path

        return self.__config_path

    def initialize(self, version, build_data):
        """
        Used by the Hatch build hook, any code in this function will run during the build process.

        Args:
        - version: The version (not used but required).
        - build_data: The build data (not used but required).
        """
        path = self.get_config_path

        process_decorator = ProcessDecorator()
        process_decorator.process_decorated_data(path_to_python_files=path)
