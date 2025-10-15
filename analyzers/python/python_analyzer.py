import os
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path
from loguru import logger
from typing import Optional, Dict, List, Union

from analyzers.base_analyzer import BaseAnalyzer
from utils import cli_utils, file_utils

class PythonCoverageAnalyzer(BaseAnalyzer):
    """
    Python coverage analyzer for pytest projects.
    """

    def __init__(self, project_path: str):
        super().__init__(language="python", project_path=project_path)

    def analyze_tests(self) -> bool:
        """
        Run pytest with coverage.
        """
        coverage_xml_path = os.path.join(self.project_path, 'coverage.xml')
        if os.path.exists(coverage_xml_path):
            os.remove(coverage_xml_path)

        cmd = ["pytest", "--cov=.", "--cov-report=xml"]
        logger.info(f"Running pytest command: {' '.join(cmd)} in {self.project_path}")
        result = cli_utils.run_cmd(cmd, exe_env=self.project_path)

        if "ERRORS" in result or "FAILURES" in result:
            logger.error(f"Pytest execution failed. Command: {' '.join(cmd)}")
            logger.error(f"Output:\n{result}")
            return False
        else:
            logger.info("Pytest execution completed successfully.")
            return True

    @staticmethod
    def parse_coverage_report_content(xml_path: Union[Path, str]) -> dict[str, dict[str, List[int]]]:
        """
        Parses the coverage.xml report to extract uncovered line and branch information.
        """
        if isinstance(xml_path, str):
            xml_path = Path(xml_path)

        if not xml_path.exists():
            logger.error(f"❌ Coverage XML report not found at expected location: {xml_path}")
            return {}

        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
        except ET.ParseError as e:
            logger.error(f"❌ Failed to parse coverage XML report {xml_path}: {e}")
            return {}
        except Exception as e:
            logger.error(f"❌ Unexpected error reading/parsing coverage XML {xml_path}: {e}", exc_info=True)
            return {}

        coverage_data = {}

        for package in root.findall('.//package'):
            for cls in package.findall('.//class'):
                file_path = cls.get('filename')
                uncovered_lines = []
                branch_uncovered_lines = []
                
                lines = cls.find('lines')
                if lines is not None:
                    for line in lines.findall('line'):
                        line_number_str = line.get('number')
                        if line_number_str is None:
                            continue
                        line_number = int(line_number_str)

                        if line.get('hits') == '0':
                            uncovered_lines.append(line_number)
                        
                        if line.get('branch') == 'true':
                            condition_coverage = line.get('condition-coverage')
                            if condition_coverage and '0%' in condition_coverage:
                                branch_uncovered_lines.append(line_number)

                coverage_data[file_path] = {
                    'uncovered': sorted(uncovered_lines),
                    'branch_uncovered': sorted(branch_uncovered_lines)
                }
        
        return coverage_data

    @staticmethod
    def get_overall_coverage(xml_path: Union[Path, str]) -> Dict[str, float]:
        """
        Parses the coverage.xml report to get overall line and branch coverage.
        """
        if isinstance(xml_path, str):
            xml_path = Path(xml_path)

        if not xml_path.exists():
            logger.error(f"❌ Coverage XML report not found at expected location: {xml_path}")
            return {}
            
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
        except ET.ParseError as e:
            logger.error(f"❌ Failed to parse coverage XML report {xml_path}: {e}")
            return {}

        line_rate = float(root.get('line-rate', 0.0)) * 100
        branch_rate = float(root.get('branch-rate', 0.0)) * 100

        return {
            "line_coverage": round(line_rate, 2),
            "branch_coverage": round(branch_rate, 2)
        }