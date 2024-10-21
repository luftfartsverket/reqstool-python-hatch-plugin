# Copyright © LFV

import os
import tarfile
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any, Dict, Optional

from hatchling.builders.hooks.plugin.interface import BuildHookInterface
from hatchling.builders.plugin.interface import BuilderInterface
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

    ARCHIVE_OUTPUT_DIR_TEST_RESULTS: str = "test_results"

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
        self.app.display_debug(f"reqstool plugin {ReqstoolBuildHook.get_version()} loaded")

        self._create_annotations_file()
        self._create_tar_gz_artifact()

    def _create_annotations_file(self) -> None:
        """
        Generates the annotations.yml file by processing the reqstool decorators.
        """
        self.app.display_debug("parsing reqstool decorators")
        sources = self.config.get("sources", [])

        decorator_processor = DecoratorProcessor()
        decorator_processor.process_decorated_data(path_to_python_files=sources)

        self.app.display_debug("generated build/reqstool/annotations.yml")

    def _create_tar_gz_artifact(self) -> None:
        """
        Creates a tar.gz artifact containing the annotations file and other necessary data.
        """

        dataset_path: Path = Path(self.config.get("dataset_path", self.INPUT_PATH_DATASET))
        junit_xml_file: Path = Path(self.config.get("junit_xml_file", self.INPUT_FILE_JUNIT_XML))
        reqstool_output_directory: Path = Path(self.config.get("output_directory", self.OUTPUT_DIR_REQSTOOL))

        file_requirements_yml: Path = Path(dataset_path, self.INPUT_FILE_REQUIREMENTS_YML)
        file_software_verification_cases_yml: Path = Path(dataset_path, self.INPUT_FILE_SOFTWARE_VERIFICATION_CASES_YML)
        file_manual_verification_results_yml: Path = Path(dataset_path, self.INPUT_FILE_MANUAL_VERIFICATION_RESULTS_YML)
        file_annotations_yml_file: Path = Path(reqstool_output_directory, self.INPUT_FILE_ANNOTATIONS_YML)

        # Define output ZIP file

        dist_dir: Path = Path(self.directory)

        tar_gz_file: Path = Path(
            dist_dir,
            f"{BuilderInterface.normalize_file_name_component(self.metadata.core.raw_name)}-"
            f"{self.metadata.version}-reqstool.tar.gz",
        )

        # Open the tar file directly with gzip compression
        with tarfile.open(tar_gz_file, "w:gz", format=tarfile.PAX_FORMAT) as archive:
            self.add_file_to_tar_gz(tar=archive, file=file_requirements_yml)
            self.add_file_to_tar_gz(tar=archive, file=file_software_verification_cases_yml)
            self.add_file_to_tar_gz(tar=archive, file=file_manual_verification_results_yml)
            self.add_file_to_tar_gz(tar=archive, file=file_annotations_yml_file)
            self.add_file_to_tar_gz(tar=archive, file=junit_xml_file, location=self.ARCHIVE_OUTPUT_DIR_TEST_RESULTS)

        self.app.display_debug(f"created {tar_gz_file}")
        self.app.display_info(os.path.relpath(tar_gz_file, dist_dir.parent))

    def add_file_to_tar_gz(self, tar: tarfile.TarFile, file: Path, location: str = None):
        if os.path.exists(file):
            arcname: Optional[Path] = os.path.basename(file) if not location else Path(location, os.path.basename(file))
            self.app.display_debug(f"adding {file}")

            tar.add(name=file, arcname=arcname, recursive=False)

    def get_version() -> str:
        try:
            ver: str = f"{version('reqstool-python-hatch-plugin')}"
        except PackageNotFoundError:
            ver: str = "package-not-found"

        return ver
