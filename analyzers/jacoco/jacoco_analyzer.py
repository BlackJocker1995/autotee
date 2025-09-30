import csv
import os
import shutil
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path
from loguru import logger

from analyzers.base_analyzer import BaseAnalyzer
from utils import cli_utils, file_utils
from typing import Optional
from typing import Union
from typing import DefaultDict, List, Dict

class JacocoAnalyzer(BaseAnalyzer):
    """
    JaCoCo analyzer for Maven projects.

    This analyzer integrates JaCoCo (Java Code Coverage) into Maven projects to
    measure code coverage during unit testing. It handles adding the JaCoCo
    plugin to pom.xml, running tests with coverage instrumentation, and
    extracting coverage reports.

    Attributes
    ----------
    project_path : str
        Path to the Maven project directory
    unit_test_items : list[dict[str, str]]
        List of test items to run, each with 'package', 'class_name', and 'name' keys
    unit_tests : str
        Comma-separated string of test identifiers formatted for Maven
    unittest_hash : str
        Hash of the unit test items used for identifying coverage reports
    determined_module_source_path : str, optional
        Path to the source directory determined during analysis
    """

    def __init__(self, project_path, unit_test_items: list[dict[str, str]], unittest_hash: Optional[str] = None):
        super().__init__(language="java", project_path=project_path)
        self.unit_test_items = unit_test_items
        # Use unit_test2str and join as string for Maven -Dtest argument
        self.unit_tests = ",".join(self.unit_test2str(unit_test_items))
        self.unittest_hash = unittest_hash if unittest_hash is not None else file_utils.hash_dict(unit_test_items)
        self.determined_module_source_path: Optional[str] = None  # Store determined source path

    @staticmethod
    def unit_test2str(unit_test_items: list[dict[str, str]]) -> list[str]:
        """
        Convert unit test items to the string format required by Maven.

        Converts test item dictionaries into Maven-compatible format strings.
        Each test item is converted to 'package.ClassName#methodName' format.

        Parameters
        ----------
        unit_test_items : list[dict[str, str]]
            List of test item dictionaries, each with 'package', 'class_name', and 'name' keys

        Returns
        -------
        list[str]
            List of Maven-compatible test identifier strings

        Example
        -------
        >>> unit_test_items = [
        ...     {'package': 'com.example', 'class_name': 'MyClass', 'name': 'testMethod'}
        ... ]
        >>> JacocoAnalyzer.unit_test2str(unit_test_items)
        ['com.example.MyClass#testMethod']
        """
        test_strings = []
        for item in unit_test_items:
            pkg = item.get('package')
            cls_name = item.get('class_name')
            method_name = item.get('name')
            if not all([pkg, cls_name, method_name]):
                logger.warning(f"Skipping test item due to missing package, class_name, or name: {item}")
                continue
            test_strings.append(f"{pkg}.{cls_name}#{method_name}")

        return test_strings

    def add_jacoco_to_project(self):
        """
        Add or update the JaCoCo plugin configuration in pom.xml.

        This method ensures that the JaCoCo Maven plugin is configured in the
        project's pom.xml file with the required executions for code coverage.
        If the plugin already exists, it updates the version and configurations.
        """
        try:
            pom_file_path = os.path.join(self.project_path, "pom.xml")
            try:
                pom_xml = file_utils.read_file(pom_file_path)
            except FileNotFoundError:
                logger.error(f"pom.xml not found at {pom_file_path}")
                raise

            self._update_pom_with_jacoco(pom_xml, pom_file_path)

        except Exception as e:
            logger.error(f"Failed to add JaCoCo to pom.xml: {str(e)}")
            raise

    def _update_pom_with_jacoco(self, pom_xml, pom_file_path):
        """
        Update pom.xml with JaCoCo plugin configuration.

        This private method handles the core logic of updating or adding the JaCoCo
        plugin configuration to the project's pom.xml file. It manages namespace
        handling for both namespaced and non-namespaced pom.xml files.

        Parameters
        ----------
        pom_xml : str
            The XML content of the pom.xml file
        pom_file_path : str
            Path to the pom.xml file to be updated
        """
        try:
            root = ET.fromstring(pom_xml)
            if root is None:
                raise ET.ParseError("Failed to parse pom.xml, root element is None.")

            namespace = ''
            if '}' in root.tag:
                namespace = root.tag.split('}')[0][1:]
                ET.register_namespace('', namespace)
                ns = {'mvn': namespace}
            else:
                ns = {}

            # Find or create the build element
            build = root.find('mvn:build' if ns else 'build', ns)
            if build is None:
                build = ET.SubElement(root, 'build')

            # Find or create the plugins element
            plugins = build.find('mvn:plugins' if ns else 'plugins', ns)
            if plugins is None:
                plugins = ET.SubElement(build, 'plugins')

            # Find the jacoco plugin if it exists
            jacoco_plugin = self._find_jacoco_plugin(plugins, ns)
            plugin_modified = self._setup_jacoco_plugin(jacoco_plugin, plugins, ns)

            if plugin_modified:
                ET.indent(root, space="  ", level=0)
                updated_pom_xml = ET.tostring(root, encoding='unicode', method='xml')
                if not updated_pom_xml.endswith('\n'):
                    updated_pom_xml += '\n'
                file_utils.write_file(pom_file_path, updated_pom_xml)
                logger.info("pom.xml updated with JaCoCo configuration.")
            else:
                logger.info("No changes needed for JaCoCo plugin in pom.xml.")

        except ET.ParseError as e:
            logger.error(f"Error parsing pom.xml: {str(e)}")
            raise Exception(f"Error parsing pom.xml: {str(e)}")
        except Exception as e:
            logger.error(f"Error processing pom.xml: {str(e)}")
            raise

    def _find_jacoco_plugin(self, plugins, ns):
        """
        Find the JaCoCo plugin in the plugins section.

        Parameters
        ----------
        plugins : xml.etree.ElementTree.Element
            The plugins element from pom.xml
        ns : dict
            Namespace dictionary for XML elements

        Returns
        -------
        xml.etree.ElementTree.Element or None
            The JaCoCo plugin element if found, otherwise None
        """
        for plugin in plugins.findall('mvn:plugin' if ns else 'plugin', ns):
            artifact_id = plugin.find('mvn:artifactId' if ns else 'artifactId', ns)
            if artifact_id is not None and artifact_id.text == 'jacoco-maven-plugin':
                logger.info("Jacoco plugin found in pom.xml")
                return plugin
        return None

    def _create_jacoco_plugin(self, plugins):
        """
        Create a new JaCoCo plugin element.

        Parameters
        ----------
        plugins : xml.etree.ElementTree.Element
            The plugins element to which the new plugin will be added

        Returns
        -------
        xml.etree.ElementTree.Element
            The newly created JaCoCo plugin element
        """
        logger.info("Jacoco plugin not found. Adding new plugin configuration.")
        jacoco_plugin = ET.SubElement(plugins, 'plugin')
        group_id = ET.SubElement(jacoco_plugin, 'groupId')
        group_id.text = 'org.jacoco'
        artifact_id = ET.SubElement(jacoco_plugin, 'artifactId')
        artifact_id.text = 'jacoco-maven-plugin'
        version = ET.SubElement(jacoco_plugin, 'version')
        version.text = '0.8.12'
        return jacoco_plugin

    def _update_jacoco_version(self, jacoco_plugin, ns):
        """
        Update JaCoCo plugin version if needed.

        Ensures the JaCoCo plugin is using the target version (0.8.12).

        Parameters
        ----------
        jacoco_plugin : xml.etree.ElementTree.Element
            The JaCoCo plugin element to update
        ns : dict
            Namespace dictionary for XML elements

        Returns
        -------
        bool
            True if the version was updated, False otherwise
        """
        version = jacoco_plugin.find('mvn:version' if ns else 'version', ns)
        target_version = '0.8.12'
        if version is not None:
            if version.text != target_version:
                version.text = target_version
                logger.info(f"Jacoco plugin version updated to {target_version}")
                return True
            else:
                logger.info(f"Jacoco plugin version is already {target_version}")
                return False
        else:
            version = ET.SubElement(jacoco_plugin, 'version')
            version.text = target_version
            logger.info(f"Jacoco plugin version added as {target_version}")
            return True

    def _add_prepare_agent_execution(self, executions, ns):
        """
        Add prepare-agent execution if it doesn't exist.

        Adds the 'prepare-agent' execution to the JaCoCo plugin configuration
        which instruments the code for coverage collection.

        Parameters
        ----------
        executions : xml.etree.ElementTree.Element
            The executions element of the JaCoCo plugin
        ns : dict
            Namespace dictionary for XML elements

        Returns
        -------
        bool
            True if execution was added, False if it already existed
        """
        prepare_agent_exists = False
        for execution in executions.findall('mvn:execution' if ns else 'execution', ns):
            id_element = execution.find('mvn:id' if ns else 'id', ns)
            if id_element is not None and id_element.text == 'prepare-agent':
                prepare_agent_exists = True
                break

        if not prepare_agent_exists:
            execution1 = ET.SubElement(executions, 'execution')
            id1 = ET.SubElement(execution1, 'id')
            id1.text = 'prepare-agent'
            goals1 = ET.SubElement(execution1, 'goals')
            goal1 = ET.SubElement(goals1, 'goal')
            goal1.text = 'prepare-agent'
            logger.info("Jacoco plugin prepare-agent execution added")
            return True
        return False

    def _add_report_execution(self, executions, ns):
        """
        Add report execution if it doesn't exist.

        Adds the 'report' execution to the JaCoCo plugin configuration which
        generates the coverage report after tests are executed.

        Parameters
        ----------
        executions : xml.etree.ElementTree.Element
            The executions element of the JaCoCo plugin
        ns : dict
            Namespace dictionary for XML elements

        Returns
        -------
        bool
            True if execution was added, False if it already existed
        """
        report_exists = False
        for execution in executions.findall('mvn:execution' if ns else 'execution', ns):
            id_element = execution.find('mvn:id' if ns else 'id', ns)
            if id_element is not None and id_element.text == 'report':
                report_exists = True
                break

        if not report_exists:
            execution2 = ET.SubElement(executions, 'execution')
            id2 = ET.SubElement(execution2, 'id')
            id2.text = 'report'
            phase2 = ET.SubElement(execution2, 'phase')
            phase2.text = 'test'
            goals2 = ET.SubElement(execution2, 'goals')
            goal2 = ET.SubElement(goals2, 'goal')
            goal2.text = 'report'
            logger.info("Jacoco plugin report execution added")
            return True
        return False

    def _setup_jacoco_plugin(self, jacoco_plugin, plugins, ns):
        """
        Set up the JaCoCo plugin with correct version and executions.

        Configures the JaCoCo plugin with the proper version and execution
        definitions required for code coverage analysis.

        Parameters
        ----------
        jacoco_plugin : xml.etree.ElementTree.Element or None
            The existing JaCoCo plugin element or None if it doesn't exist
        plugins : xml.etree.ElementTree.Element
            The plugins element in pom.xml
        ns : dict
            Namespace dictionary for XML elements

        Returns
        -------
        bool
            True if the plugin configuration was modified, False otherwise
        """
        plugin_modified = False

        # Update or create jacoco plugin
        if jacoco_plugin is None:
            jacoco_plugin = self._create_jacoco_plugin(plugins)
            plugin_modified = True
        else:
            # Update version if needed
            plugin_modified = self._update_jacoco_version(jacoco_plugin, ns) or plugin_modified

        # Set up executions
        executions = jacoco_plugin.find('mvn:executions' if ns else 'executions', ns)
        if executions is None:
            executions = ET.SubElement(jacoco_plugin, 'executions')
            plugin_modified = True

        plugin_modified = self._add_prepare_agent_execution(executions, ns) or plugin_modified
        plugin_modified = self._add_report_execution(executions, ns) or plugin_modified

        return plugin_modified

    def analyze_tests(self):
        """
        Run specified Maven tests with JaCoCo agent.

        Executes the configured Maven tests with JaCoCo instrumentation enabled
        to collect code coverage data. This method runs the tests and determines
        the source path for coverage analysis.

        Returns
        -------
        bool or None
            False if the build or tests fail, None otherwise
        """
        dest_file = os.path.join(self.project_path, 'database', f'{len(self.unit_test_items)}', f"{self.unittest_hash}.xml")
        if os.path.exists(dest_file):
            logger.info(f"Coverage file {dest_file} exists, skipping analysis.")
            return

        if not self.unit_tests:
            logger.warning("No valid Maven test filters found to execute.")
            return

        cmd = ["mvn", "clean", "test", f"-Dtest={self.unit_tests}"]
        logger.info(f"Running Maven command: {' '.join(cmd)} in {self.project_path}")
        result = cli_utils.run_cmd(cmd, exe_env=self.project_path)

        if "BUILD FAILURE" in result or "[ERROR] Tests run:" in result and ", Failures: [1-9]" in result:
             logger.error(f"Maven build failed or tests failed. Command: {' '.join(cmd)}")
             logger.error(f"Output:\n{result}")
             return False
        else:
             logger.info("Maven test execution completed successfully.")
             self._determine_maven_source_path()

    def _determine_maven_source_path(self):
        """
        Try to determine the source path for Maven projects.

        Looks for the conventional Maven source directory (src/main/java) and
        sets it as the determined source path. If not found, logs a warning
        and sets the path to None to trigger heuristic detection.
        """
        root_src_dir = Path(self.project_path) / 'src' / 'main' / 'java'
        if root_src_dir.is_dir():
            self.determined_module_source_path = str(root_src_dir.resolve())
            logger.info(f"Determined Maven project source path: {self.determined_module_source_path}")
        else:
            logger.warning(f"Conventional source path '{root_src_dir}' not found for Maven project. Debloat will use heuristics.")
            self.determined_module_source_path = None

    def get_determined_module_source_path(self) -> Optional[str]:
        """
        Return the absolute path of the source directory determined during analysis.

        If the source path hasn't been determined yet, this method will attempt
        to determine it. This typically returns the path to src/main/java for
        standard Maven projects.

        Returns
        -------
        str or None
            Absolute path to the source directory or None if not determined
        """
        if self.determined_module_source_path is None:
            logger.warning("Attempting to get module source path before analyze_tests determined it. Trying now.")
            self._determine_maven_source_path()
        return self.determined_module_source_path

    def _find_maven_report_path(self) -> Path | None:
        """
        Find the path to the JaCoCo XML report for Maven.

        Looks for the JaCoCo XML report generated during Maven test execution
        in the standard location (target/site/jacoco/jacoco.xml).

        Returns
        -------
        pathlib.Path or None
            Path to the JaCoCo XML report or None if not found
        """
        project_path_obj = Path(self.project_path)
        source_file_path = project_path_obj / 'target/site/jacoco/jacoco.xml'
        if source_file_path.exists():
            logger.info(f"Found Maven JaCoCo report at: {source_file_path}")
            return source_file_path
        else:
            logger.error(f"Could not find Maven JaCoCo XML report at expected location: {source_file_path}")
            return None

    def copy_coverage_xml(self):
        """
        Copy the generated JaCoCo XML report to the database directory.

        Copies the JaCoCo coverage report from the Maven-generated location
        to the project's database directory for later analysis.
        """
        dest_file_path = os.path.join(self.project_path, 'database', f'{len(self.unit_test_items)}', f"{self.unittest_hash}.xml")
        if os.path.exists(dest_file_path):
            logger.info(f"Destination file {dest_file_path} exists, skipping copy.")
            return
        dest_dir = os.path.dirname(dest_file_path)
        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir)

        source_file_path = self._find_maven_report_path()
        source_file_str = str(source_file_path) if source_file_path else None

        if source_file_str and os.path.exists(source_file_str):
            if not os.path.exists(dest_file_path):
                shutil.copy(source_file_str, dest_file_path)
                logger.info(f"Copied JaCoCo report from {source_file_str} to {dest_file_path}")
        else:
             if not source_file_str:
                  logger.error("Error: JaCoCo XML file could not be located for Maven project.")
             elif not os.path.exists(source_file_str):
                  logger.error(f"Error: Located source file path does not exist: {source_file_str}")

    @classmethod
    def parse_jacoco_report(cls, report_path: str) -> dict[str, float]:
        """
        Extract line and branch coverage from a JaCoCo CSV report.

        Parses a JaCoCo CSV report file to extract line and branch coverage
        percentages. The CSV should contain columns LINE_MISSED, LINE_COVERED,
        BRANCH_MISSED, and BRANCH_COVERED.

        Parameters
        ----------
        report_path : str
            Path to the JaCoCo CSV file (generated with `--csv` or `jacocoReportType=csv`)

        Returns
        -------
        dict[str, float]
            Dictionary containing coverage percentages with keys 'line_coverage'
            and 'branch_coverage', rounded to two decimal places. Returns empty
            dict if parsing fails.

        Example
        -------
        >>> coverage_data = JacocoAnalyzer.parse_jacoco_report('/path/to/report.csv')
        >>> print(coverage_data)
        {'line_coverage': 85.5, 'branch_coverage': 72.3}
        """
        # 1️Verify the file exists
        if not os.path.exists(report_path):
            logger.error(f"JaCoCo CSV report not found at {report_path}")
            return {}

        try:
            # Open the CSV and read the header
            with open(report_path, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)

                #  Ensure the required columns are present
                required = {"LINE_MISSED", "LINE_COVERED",
                            "BRANCH_MISSED", "BRANCH_COVERED"}
                if not required.issubset(set(reader.fieldnames or [])):
                    missing = required - set(reader.fieldnames or [])
                    raise ValueError(f"CSV is missing columns: {missing}")

                total_line_covered = 0
                total_line_missed = 0
                total_branch_covered = 0
                total_branch_missed = 0
                
                # Iterate over all rows and sum up the coverage data
                for row in reader:
                    try:
                        total_line_covered += int(row["LINE_COVERED"])
                        total_line_missed += int(row["LINE_MISSED"])
                        total_branch_covered += int(row["BRANCH_COVERED"])
                        total_branch_missed += int(row["BRANCH_MISSED"])
                    except ValueError as ve:
                        logger.warning(f"Skipping row due to invalid integer conversion: {row}. Error: {ve}")
                        continue

                # Compute totals
                total_lines = total_line_covered + total_line_missed
                total_branches = total_branch_covered + total_branch_missed

                
                
                
                # Calculate percentages
                line_coverage = (
                    round((total_line_covered / total_lines) * 100, 2)
                    if total_lines > 0
                    else 0.0
                )
                
                if total_branches == 0:
                    # No branches found in code — not "0% coverage", but "N/A"
                    branch_coverage = 100  # or float('nan'), or omit key
                else:
                    branch_coverage = round((total_branch_covered / total_branches) * 100, 2)
                

                # Log the results
                logger.info(
                    f"Parsed JaCoCo CSV: Line Coverage = {line_coverage}% | "
                    f"Branch Coverage = {branch_coverage}%"
                )

                return {
                    "line_coverage": line_coverage,
                    "branch_coverage": branch_coverage,
                }

        except csv.Error as e:
            logger.error(f"CSV parsing error for {report_path}: {e}")
        except ValueError as e:
            logger.error(f"Data error in {report_path}: {e}")
        except Exception as e:
            logger.exception(
                f"Unexpected error while parsing JaCoCo CSV report {report_path}: {e}"
            )

        return {}


    @staticmethod
    def parse_jacoco_report_content(xml_path: Union[Path, str]) -> dict[str, dict[str, List[int]]]:
        """
        Parses the Jacoco XML report to extract uncovered line and branch information.

        Args:
            xml_path (Path): The path to the Jacoco XML report.

        Returns:
            Dict[str, Dict[str, List[int]]]: A dictionary mapping package-relative paths to
            coverage details including uncovered lines and branch uncovered lines.
            Returns empty dict on critical errors.
        """
        if isinstance(xml_path, str):
                xml_path = Path(xml_path)

        # Parse the XML report
        if not xml_path.exists():
            logger.error(f"❌ Jacoco XML report not found at expected location: {xml_path}")
            return {}

        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
        except ET.ParseError as e:
            logger.error(f"❌ Failed to parse Jacoco XML report {xml_path}: {e}")
            return {}
        except Exception as e:
            logger.error(f"❌ Unexpected error reading/parsing Jacoco XML {xml_path}: {e}", exc_info=True)
            return {}

        # 5. Process coverage data
        coverage_data: DefaultDict[str, Dict[str, List[int]]] = defaultdict(lambda: {
            'uncovered': [],
            'branch_uncovered': []
        })
        files_processed = 0
        files_skipped = 0
        files_excluded = 0 # New counter for files excluded due to no coverage

        for package_element in root.findall('.//package'):
            package_name = package_element.get('name')
            if not package_name:
                logger.warning("Found package element with no 'name' attribute, skipping.")
                files_skipped += len(package_element.findall('sourcefile')) # Estimate skipped
                continue

            for sourcefile in package_element.findall('sourcefile'):
                source_file_name = sourcefile.get('name')
                if not source_file_name:
                    logger.warning(f"Found sourcefile element with no 'name' attribute in package '{package_name}', skipping.")
                    files_skipped += 1
                    continue

                try:
                    # Determine if the file has any line or branch coverage
                    # Determine if the file has any line or branch coverage by checking counters
                    line_counter = sourcefile.find('counter[@type="LINE"]')
                    branch_counter = sourcefile.find('counter[@type="BRANCH"]')

                    # Exclude if no line or branch coverage metrics are reported
                    if (line_counter is None or int(line_counter.get('covered', 0)) == 0) and \
                       (branch_counter is None or int(branch_counter.get('covered', 0)) == 0):
                        logger.debug(f"Excluding file '{source_file_name}' due to no line or branch coverage.")
                        files_excluded += 1
                        continue

                    # Construct path relative to source root and convert to posix string inline
                    # Use the path relative to the source directory (src/main/java) as the key
                    # This aligns with Coverlet and the expectation of copy_source_files
                    path_str = (Path(package_name.replace('.', '/')) / source_file_name).as_posix() # e.g., org/cryptomator/logging/LogbackConfiguratorFactory.java

                    # Extract and sort uncovered lines safely
                    uncovered_lines_int = sorted([int(nr) for line in sourcefile.findall('line') if int(line.get('mi', 0)) > 0 and (nr := line.get('nr')) is not None])

                    # Extract and sort branch uncovered data
                    branch_uncovered_lines_int = []

                    # Process branch coverage data
                    for line in sourcefile.findall('line'):
                        nr = line.get('nr')
                        if not nr:
                            continue
                        nr_int = int(nr)

                        # Get branch coverage data
                        mb = line.get('mb', 0)  # missed branches

                        if int(mb) > 0:
                            branch_uncovered_lines_int.append(nr_int)

                    # Always populate the result dictionary for the file, even if no lines are covered
                    coverage_data[path_str]['uncovered'] = uncovered_lines_int
                    coverage_data[path_str]['branch_uncovered'] = sorted(branch_uncovered_lines_int)
                    files_processed += 1


                except (ValueError, TypeError) as e: # Catch potential int conversion errors
                    logger.warning(f"❌ Error processing line numbers for '{source_file_name}' in package '{package_name}': {e}. Skipping file.")
                    files_skipped += 1
                except Exception as e:
                    logger.warning(f"❌ Unexpected error processing sourcefile '{source_file_name}' in package '{package_name}': {e}", exc_info=True)
                    files_skipped += 1

        logger.info(f"Enhanced Jacoco report parsing complete. Processed entries for {files_processed} files, skipped {files_skipped} entries due to issues, excluded {files_excluded} files due to no coverage.")
        return dict(coverage_data)
