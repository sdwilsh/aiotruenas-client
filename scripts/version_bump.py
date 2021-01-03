import argparse
import configparser
import os
import subprocess
from packaging.version import Version

CONFIG_FILE = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), "..", "setup.cfg"
)


def init_argparse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Cuts a new release branch.",
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument(
        "--ignore-untracked-files",
        action="store_true",
        help="Ignores any untracked files from `git status` and cuts a release anyway.",
    )
    return parser


def has_clean_git_status(ignore_untracked: bool) -> bool:
    r = subprocess.run(
        ["git", "status", "--porcelain"], check=True, capture_output=True, text=True
    )
    for line in r.stdout.strip().splitlines():
        if ignore_untracked and line.startswith("??"):
            continue
        return False
    return True


def checkout_main_branch() -> None:
    subprocess.run(["git", "fetch"], check=True)
    subprocess.run(["git", "checkout", "-b", "version-bump", "origin/main"], check=True)


def get_current_revision(verbose: bool) -> str:
    r = subprocess.run(
        ["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True
    )
    rev = r.stdout.strip()
    if verbose:
        print(f"`git rev-parse HEAD`: {rev}")
    return rev


def get_current_version() -> Version:
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)
    return Version(config["metadata"]["version"])


def get_release_version(current_version: Version) -> Version:
    return Version(current_version.base_version)


def get_next_version(current_version: Version) -> Version:
    return Version(
        ".".join([str(current_version.major), str(current_version.minor + 1), "0a"])
    )


def write_version_to_file(version: Version, verbose: bool) -> None:
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)
    config["metadata"]["version"] = str(version)
    with open(CONFIG_FILE, "w") as config_file:
        config.write(config_file)
    if verbose:
        print(f"Updated {CONFIG_FILE} to version {version}")


def cut_release_branch(release_version: Version, verbose: bool) -> None:
    pre_release_rev = get_current_revision(verbose)
    print(f"Cutting release {release_version} from {pre_release_rev}")
    write_version_to_file(release_version, verbose)
    subprocess.run(["git", "add", CONFIG_FILE], check=True)
    subprocess.run(
        [
            "git",
            "commit",
            "-m",
            f"""Cut release for {release_version}

Based on {pre_release_rev}
""",
        ],
        check=True,
    )
    subprocess.run(
        [
            "git",
            "push",
            "origin",
            f"HEAD:refs/heads/v{release_version.major}.{release_version.minor}",
        ],
        check=True,
    )
    print(
        f"Release branch for v{release_version.major}.{release_version.minor} has been created."
    )
    print(
        f"Please go to https://github.com/sdwilsh/aiotruenas-client/releases/new to create a new release for v{release_version.major}.{release_version.minor}."
    )
    subprocess.run(["git", "reset", "--hard", pre_release_rev], check=True)


def update_main_branch(
    next_version: Version, release_version: Version, verbose: bool
) -> None:
    print(
        f"Updating main to use version {next_version} now that {release_version} is branched."
    )
    write_version_to_file(next_version, verbose)
    subprocess.run(["git", "add", CONFIG_FILE])
    subprocess.run(
        [
            "git",
            "commit",
            "-m",
            f"""Version bump to {next_version}

v{release_version.major}.{release_version.minor} branch has been cut.""",
        ],
        check=True,
    )
    subprocess.run(
        [
            "git",
            "push",
            "origin",
            f"HEAD:refs/heads/v{next_version}-version-bump",
        ],
        check=True,
    )
    print(
        f"Please go to https://github.com/sdwilsh/aiotruenas-client/pull/new/v{next_version}-version-bump to open a pull request."
    )


if __name__ == "__main__":
    parser = init_argparse()
    args = parser.parse_args()
    if not has_clean_git_status(args.ignore_untracked_files):
        print("`git status` shows untracked files!")
        exit(1)
    checkout_main_branch()
    current_version = get_current_version()
    release_version = get_release_version(current_version)
    next_version = get_next_version(current_version)
    cut_release_branch(release_version, args.verbose)
    assert has_clean_git_status(args.ignore_untracked_files)
    update_main_branch(next_version, release_version, args.verbose)
    assert has_clean_git_status(args.ignore_untracked_files)
