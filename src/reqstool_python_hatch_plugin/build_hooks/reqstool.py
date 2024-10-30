# Copyright © LFV

import gzip
import io
import os
import tarfile
import tempfile
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any, Dict, List, Optional

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

    CONFIG_SOURCES = "sources"
    CONFIG_DATASET_DIRECTORY = "dataset_directory"
    CONFIG_OUTPUT_DIRECTORY = "output_directory"
    CONFIG_TEST_RESULTS: str = "test_results"

    INPUT_FILE_REQUIREMENTS_YML: str = "requirements.yml"
    INPUT_FILE_SOFTWARE_VERIFICATION_CASES_YML: str = "software_verification_cases.yml"
    INPUT_FILE_MANUAL_VERIFICATION_RESULTS_YML: str = "manual_verification_results.yml"
    INPUT_FILE_JUNIT_XML: str = "build/junit.xml"
    INPUT_FILE_ANNOTATIONS_YML: str = "annotations.yml"
    INPUT_DIR_DATASET: str = "reqstool"

    OUTPUT_DIR_REQSTOOL: str = "build/reqstool"
    OUTPUT_SDIST_REQSTOOL_YML: str = "reqstool_config.yml"

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
        self.app.display_info(f"[reqstool] plugin {ReqstoolBuildHook.get_version()} loaded")

        self._create_annotations_file()

    def finalize(self, version: str, build_data: dict[str, Any], artifact_path: str) -> None:

        if artifact_path.endswith(".tar.gz"):
            self._append_to_sdist_tar_gz(version=version, build_data=build_data, artifact_path=artifact_path)

    def _create_annotations_file(self) -> None:
        """
        Generates the annotations.yml file by processing the reqstool decorators.
        """
        self.app.display_debug("[reqstool] parsing reqstool decorators")
        sources = self.config.get(self.CONFIG_SOURCES, [])

        reqstool_output_directory: Path = Path(self.config.get(self.CONFIG_OUTPUT_DIRECTORY, self.OUTPUT_DIR_REQSTOOL))
        annotations_file: Path = Path(reqstool_output_directory, self.INPUT_FILE_ANNOTATIONS_YML)

        decorator_processor = DecoratorProcessor()
        decorator_processor.process_decorated_data(path_to_python_files=sources, output_file=annotations_file)

        self.app.display_debug(f"[reqstool] generated {str(annotations_file)}")

    def _append_to_sdist_tar_gz(self, version: str, build_data: Dict[str, Any], artifact_path: str) -> None:
        """
        Appends to sdist containing the annotations file and other necessary data.
        """
        dataset_directory: Path = Path(self.config.get(self.CONFIG_DATASET_DIRECTORY, self.INPUT_DIR_DATASET))
        reqstool_output_directory: Path = Path(self.config.get(self.CONFIG_OUTPUT_DIRECTORY, self.OUTPUT_DIR_REQSTOOL))
        test_result_patterns: List[str] = self.config.get(self.CONFIG_TEST_RESULTS, [])
        requirements_file: Path = Path(dataset_directory, self.INPUT_FILE_REQUIREMENTS_YML)
        svcs_file: Path = Path(dataset_directory, self.INPUT_FILE_SOFTWARE_VERIFICATION_CASES_YML)
        mvrs_file: Path = Path(dataset_directory, self.INPUT_FILE_MANUAL_VERIFICATION_RESULTS_YML)
        annotations_file: Path = Path(reqstool_output_directory, self.INPUT_FILE_ANNOTATIONS_YML)

        resources: Dict[str, str] = {}

        if not os.path.exists(requirements_file):
            msg: str = f"[reqstool] missing mandatory {self.INPUT_FILE_REQUIREMENTS_YML}: {requirements_file}"
            raise RuntimeError(msg)

        resources["requirements"] = str(requirements_file)
        self.app.display_debug(f"[reqstool] added to {self.OUTPUT_SDIST_REQSTOOL_YML}: {requirements_file}")

        if os.path.exists(svcs_file):
            resources["software_verification_cases"] = str(svcs_file)
            self.app.display_debug(f"[reqstool] added to {self.OUTPUT_SDIST_REQSTOOL_YML}: {svcs_file}")

        if os.path.exists(mvrs_file):
            resources["manual_verification_results"] = str(mvrs_file)
            self.app.display_debug(f"[reqstool] added to {self.OUTPUT_SDIST_REQSTOOL_YML}: {mvrs_file}")

        if os.path.exists(annotations_file):
            resources["annotations"] = str(annotations_file)
            self.app.display_debug(f"[reqstool] added to {self.OUTPUT_SDIST_REQSTOOL_YML}: {annotations_file}")

        if test_result_patterns:
            resources["test_results"] = test_result_patterns
            self.app.display_debug(
                f"[reqstool] added test_results to {self.OUTPUT_SDIST_REQSTOOL_YML}: {test_result_patterns}"
            )

        reqstool_yaml_data = {"language": "python", "build": "hatch", "resources": resources}

        yaml = YAML()
        yaml.default_flow_style = False
        reqstool_yml_io = io.BytesIO()
        reqstool_yml_io.write(f"{self.YAML_LANGUAGE_SERVER}\n".encode("utf-8"))
        reqstool_yml_io.write(f"# version: {self.metadata.version}\n".encode("utf-8"))

        self.app.display_debug(f"[reqstool] reqstool config {reqstool_yaml_data}")

        yaml.dump(reqstool_yaml_data, reqstool_yml_io)
        reqstool_yml_io.seek(0)

        # Path to the existing tar.gz file (constructed from metadata)
        original_tar_gz_file = os.path.join(
            self.directory,
            f"{BuilderInterface.normalize_file_name_component(self.metadata.core.raw_name)}"
            f"-{self.metadata.version}.tar.gz",
        )

        self.app.display_debug(f"[reqstool] tarball: {original_tar_gz_file}")

        # Step 1: Extract the original tar.gz file to a temporary directory
        with tempfile.NamedTemporaryFile(delete=True) as temp_tar_file:

            temp_tar_file = temp_tar_file.name  # Get the name of the temporary file

            self.app.display_debug(f"[reqstool] temporary tar file: {temp_tar_file}")

            # Extract the original tar.gz file
            with gzip.open(original_tar_gz_file, "rb") as f_in, open(temp_tar_file, "wb") as f_out:
                f_out.write(f_in.read())

            # Step 2: Open the extracted tar file and append the new file
            with tarfile.open(temp_tar_file, "a") as archive:
                file_info = tarfile.TarInfo(
                    name=f"{BuilderInterface.normalize_file_name_component(self.metadata.core.raw_name)}-"
                    f"{self.metadata.version}/{self.OUTPUT_SDIST_REQSTOOL_YML}"
                )
                file_info.size = reqstool_yml_io.getbuffer().nbytes
                archive.addfile(tarinfo=file_info, fileobj=reqstool_yml_io)

            # Step 3: Recompress the updated tar file back into the original .tar.gz format
            with open(temp_tar_file, "rb") as f_in, gzip.open(original_tar_gz_file, "wb") as f_out:
                f_out.writelines(f_in)

        dist_dir: Path = Path(self.directory)
        self.app.display_info(
            f"[reqstool] added {self.OUTPUT_SDIST_REQSTOOL_YML} to "
            f"{os.path.relpath(original_tar_gz_file, dist_dir.parent)}"
        )

    def get_version() -> str:
        try:
            ver: str = f"{version('reqstool-python-hatch-plugin')}"
        except PackageNotFoundError:
            ver: str = "package-not-found"

        return ver
