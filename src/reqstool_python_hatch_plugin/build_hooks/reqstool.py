# Copyright © LFV

import tarfile
from pathlib import Path
from typing import Any, Dict, Optional

from hatchling.builders.hooks.plugin.interface import BuildHookInterface
from reqstool_python_decorators.processors.decorator_processor import DecoratorProcessor


class ReqstoolBuildHook(BuildHookInterface):
    """
    Build hook that creates reqstool

    1. annotations files based on reqstool decorators
    2. artifact reqstool-tar.gz file to be uploaded by hatch publish to pypi repo

    Attributes:
        PLUGIN_NAME (str): The name of the plugin, set to "reqstool".
    """

    PLUGIN_NAME: str = "reqstool"

    INPUT_FILE_REQUIREMENTS_YML: str = "requirements.yml"
    INPUT_FILE_SOFTWARE_VERIFICATION_CASES_YML: str = "software_verification_cases.yml"
    INPUT_FILE_MANUAL_VERIFICATION_RESULTS_YML: str = "manual_verification_results.yml"
    INPUT_FILE_JUNIT_XML: str = "build/junit.xml"
    INPUT_FILE_ANNOTATIONS_YML: str = "annotations.yml"
    INPUT_PATH_DATASET: str = "reqstool"
    OUTPUT_DIR_REQSTOOL: str = "build/reqstool"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.__config_path: Optional[str] = None

    def initialize(self, version: str, build_data: Dict[str, Any]) -> None:
        """
        Executes custom actions during the build process.

        Args:
            version (str): The version of the project.
            build_data (dict): The build-related data.
        """
        self.app.display_info(f"reqstool plugin {version} loaded")

        self._create_annotations_file()
        self._create_tar_gz_artifact()

    def _create_annotations_file(self) -> None:
        """
        Generates the annotations.yml file by processing the reqstool decorators.
        """
        self.app.display_info("parsing reqstool decorators")
        sources = self.config.get("sources", [])

        decorator_processor = DecoratorProcessor()
        decorator_processor.process_decorated_data(path_to_python_files=sources)

        self.app.display_info("generated build/reqstool/annotations.yml")

    def _create_tar_gz_artifact(self) -> None:
        """
        Creates a tar.gz artifact containing the annotations file and other necessary data.
        """

        dataset_path: Path = Path(self.config.get("dataset_path", self.INPUT_PATH_DATASET))
        junit_xml_file: Path = Path(self.config.get("junit_xml_file", self.INPUT_FILE_JUNIT_XML))
        reqstool_output_directory: Path = Path(self.config.get("output_directory", self.OUTPUT_DIR_REQSTOOL))

        file_requirements_yml: Path = Path(dataset_path, self.INPUT_FILE_REQUIREMENTS_YML)
        file_software_verification_cases_ymlPath = Path(dataset_path, self.INPUT_FILE_SOFTWARE_VERIFICATION_CASES_YML)
        file_manual_verification_results_ymlPath = Path(dataset_path, self.INPUT_FILE_MANUAL_VERIFICATION_RESULTS_YML)
        file_annotations_yml_filePath = Path(self.directory, self.INPUT_FILE_ANNOTATIONS_YML)

        # Define output ZIP file
        tar_gz_file: Path = Path(self.directory, "reqstool-artifactg.tar.gz")

        with tarfile.open(tar_gz_file, "w:gz") as tar:
            # Add files to the ZIP archive
            if os.path.exists(requirements_annotations_file):
                self.app.display_info(f"adding {requirements_annotations_file}")
                tar.add(requirements_annotations_file, os.path.basename(requirements_annotations_file))

            if os.path.exists(dataset_path):
                for root, _, files in os.walk(dataset_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        tar.add(file_path, os.path.relpath(file_path, dataset_path))

            # Include junit report directory
            if os.path.exists(junit_reports_dir):
                for root, _, files in os.walk(junit_reports_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        tar.add(file_path, os.path.relpath(file_path, junit_reports_dir))

        print(f"created {tar_gz_file}")
