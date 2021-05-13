import os
import unittest
from typing import List, Tuple

import pkg_resources
import yaml

PRE_COMMIT_CONFIG_FILE = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), "..", ".pre-commit-config.yaml"
)
REQUIREMENTS_DEV_FILE = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), "..", "requirements-dev.txt"
)


class TestRequirements(unittest.TestCase):
    def test_pre_commit_synced(self) -> None:
        pre_commit_versions = {r[0]: r[1] for r in self._get_pre_commit_config_data()}
        requirements_dev_versions = {
            r[0]: r[1] for r in self._get_requirements_dev_data()
        }
        for name in pre_commit_versions:
            self.assertEqual(
                pre_commit_versions[name],
                requirements_dev_versions[name],
                f"The version of {name} must match in `.pre-commit-config.yaml` ({pre_commit_versions[name][0][1]}) and `requirements-dev.txt` ({requirements_dev_versions[name][0][1]})",
            )

    def _get_pre_commit_config_data(self) -> List[Tuple[str, List[Tuple[str, str]]]]:
        with open(PRE_COMMIT_CONFIG_FILE, "r") as config:
            repos_config = yaml.full_load(config)["repos"]
            r = []
            for repo in repos_config:
                for hook in repo["hooks"]:
                    if hook["language_version"] != "python3":
                        continue
                    r.append((hook["id"], [("==", repo["rev"].lstrip("v"))]))
            return r

    def _get_requirements_dev_data(self) -> List[Tuple[str, List[Tuple[str, str]]]]:
        with open(REQUIREMENTS_DEV_FILE, "r") as requirements:
            return [
                (req.key, req.specs)
                for req in pkg_resources.parse_requirements(requirements)
            ]


if __name__ == "__main__":
    unittest.main()
