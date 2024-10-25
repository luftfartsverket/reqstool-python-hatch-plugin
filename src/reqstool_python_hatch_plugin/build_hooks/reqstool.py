# Copyright © LFV

import gzip
import io
import os
import tarfile
import tempfile
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any, Dict, Optional

from hatchling.builders.hooks.plugin.interface import BuildHookInterface
from hatchling.builders.plugin.interface import BuilderInterface
from reqstool_python_decorators.processors.decorator_processor import DecoratorProcessor
from ruamel.yaml import YAML


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
    OUTPUT_SDIST_REQSTOOL_YML: str = "reqstool_index.yml"

    ARCHIVE_OUTPUT_DIR_TEST_RESULTS: str = "test_results"

    YAML_LANGUAGE_SERVER = "# yaml-language-server: $schema=https://raw.githubusercontent.com/Luftfartsverket/reqstool-client/main/src/reqstool/resources/schemas/v1/reqstool_index.schema.json\n"  # noqa: E501

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
        self.app.display_info(f"reqstool plugin {ReqstoolBuildHook.get_version()} loaded")

        self._create_annotations_file()

    def finalize(self, version: str, build_data: dict[str, Any], artifact_path: str) -> None:

        if artifact_path.endswith(".tar.gz"):
            self._append_to_sdist_tar_gz(version=version, build_data=build_data, artifact_path=artifact_path)

    def _create_annotations_file(self) -> None:
        """
        Generates the annotations.yml file by processing the reqstool decorators.
        """
        self.app.display_debug("parsing reqstool decorators")
        sources = self.config.get("sources", [])

        decorator_processor = DecoratorProcessor()
        decorator_processor.process_decorated_data(path_to_python_files=sources)

        self.app.display_debug("generated build/reqstool/annotations.yml")

    def _append_to_sdist_tar_gz(self, version: str, build_data: Dict[str, Any], artifact_path: str) -> None:
        """
        Appends to sdist containing the annotations file and other necessary data.
        """
        dataset_path: Path = Path(self.config.get("dataset_path", self.INPUT_PATH_DATASET))
        reqstool_output_directory: Path = Path(self.config.get("output_directory", self.OUTPUT_DIR_REQSTOOL))

        yaml_data = {
            "language": "python",
            "build": "hatch",
            "version": self.metadata.version,
            "resources": {
                "requirements": str(Path(dataset_path, self.INPUT_FILE_REQUIREMENTS_YML)),
                "software_verification_cases": str(Path(dataset_path, self.INPUT_FILE_SOFTWARE_VERIFICATION_CASES_YML)),
                "manual_verification_results": str(Path(dataset_path, self.INPUT_FILE_MANUAL_VERIFICATION_RESULTS_YML)),
                "annotations": str(Path(reqstool_output_directory, self.INPUT_FILE_ANNOTATIONS_YML)),
                "test_results": [str(Path(self.config.get("junit_xml_file", self.INPUT_FILE_JUNIT_XML)))],
            },
        }

        yaml = YAML()
        yaml.default_flow_style = False
        reqstool_yml = io.BytesIO()
        # Write the YAML_LANGUAGE_SERVER value as the first line
        reqstool_yml.write(f"{self.YAML_LANGUAGE_SERVER}\n".encode("utf-8"))
        yaml.dump(yaml_data, reqstool_yml)
        reqstool_yml.seek(0)

        self.app.display_debug(f"reqstool index: {yaml_data}")

        # Path to the existing tar.gz file (constructed from metadata)
        original_tar_gz_file = os.path.join(
            self.directory,
            f"{BuilderInterface.normalize_file_name_component(self.metadata.core.raw_name)}"
            f"-{self.metadata.version}.tar.gz",
        )

        self.app.display_debug(f"tarball: {original_tar_gz_file}")

        # Step 1: Extract the original tar.gz file to a temporary directory
        with tempfile.NamedTemporaryFile(delete=True) as temp_tar_file:

            temp_tar_file = temp_tar_file.name  # Get the name of the temporary file

            self.app.display_debug(f"temporary tar file: {temp_tar_file}")

            # Extract the original tar.gz file
            with gzip.open(original_tar_gz_file, "rb") as f_in, open(temp_tar_file, "wb") as f_out:
                f_out.write(f_in.read())

            # Step 2: Open the extracted tar file and append the new file
            with tarfile.open(temp_tar_file, "a") as archive:
                file_info = tarfile.TarInfo(
                    name=f"{BuilderInterface.normalize_file_name_component(self.metadata.core.raw_name)}-"
                    f"{self.metadata.version}/{self.OUTPUT_SDIST_REQSTOOL_YML}"
                )
                file_info.size = reqstool_yml.getbuffer().nbytes
                archive.addfile(tarinfo=file_info, fileobj=reqstool_yml)

            # Step 3: Recompress the updated tar file back into the original .tar.gz format
            with open(temp_tar_file, "rb") as f_in, gzip.open(original_tar_gz_file, "wb") as f_out:
                f_out.writelines(f_in)

        dist_dir: Path = Path(self.directory)
        self.app.display_info(f"added reqstool_index.yml to {os.path.relpath(original_tar_gz_file, dist_dir.parent)}")

    def get_version() -> str:
        try:
            ver: str = f"{version('reqstool-python-hatch-plugin')}"
        except PackageNotFoundError:
            ver: str = "package-not-found"

        return ver
