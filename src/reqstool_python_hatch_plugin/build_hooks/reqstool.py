# Copyright © LFV

from hatchling.builders.hooks.plugin.interface import BuildHookInterface
from reqstool_python_decorators.processors.decorator_processor import DecoratorProcessor


class ReqstoolBuildHook(BuildHookInterface):
    """
    Build hook that creates reqstool

    1. annotations files based on reqstool decorators
    2. artifact reqstool-tar.gz file to be uploaded by hatch publish to pypi repo

    Attributes:
        PLUGIN_NAME (str): The name of the plugin, set to "reqstool".

    Methods:
        initialize(version, build_data):
            Executes custom actions during the build process, such as processing decorated Python files.
    """

    PLUGIN_NAME = "reqstool"

    # https://github.com/ofek/hatch-autorun/blob/master/src/hatch_autorun/plugin.py
    # build/reqstool/annotations.yml

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__config_path = None

    def initialize(self, version, build_data):
        self.app.display_info(f"reqstool plugin {version} loaded")

        self._create_annotations_file()

        self._create_zip_artifact()

    def _create_annotations_file(self):
        self.app.display_info("parsing reqstool decorators")

        path = self.config.get("path", [])

        decorator_processor = DecoratorProcessor()
        decorator_processor.process_decorated_data(path_to_python_files=path)

        self.app.display_info("generated build/reqstool/annotations.yml")

    def _create_zip_artifact(self):
        requirements_annotations_file = "build/reqstool/annotations.yml"

        # Define output ZIP file
        zipfile_name = os.path.join(output_directory, "build_output.zip")

        # Create ZIP file
        with zipfile.ZipFile(zipfile_name, "w", zipfile.ZIP_DEFLATED) as zipf:
            # Add files to the ZIP archive
            if os.path.exists(requirements_annotations_file):
                zipf.write(requirements_annotations_file, os.path.basename(requirements_annotations_file))

            if os.path.exists(dataset_path):
                for root, _, files in os.walk(dataset_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        zipf.write(file_path, os.path.relpath(file_path, dataset_path))

            # Include junit report directory
            if os.path.exists(junit_reports_dir):
                for root, _, files in os.walk(junit_reports_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        zipf.write(file_path, os.path.relpath(file_path, junit_reports_dir))

        print(f"ZIP file created: {zipfile_name}")
        return artifacts
