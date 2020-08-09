"""pyfreenas setup script."""
from setuptools import setup

version = "0.1.0"

github_username = "sdwilsh"
github_repository = "py-freenas"

github_path = f"{github_username}/{github_repository}"
github_url = f"https://github.com/{github_path}"

download_url = f"{github_url}/archive/{version}.tar.gz"
project_urls = {"Bug Reports": f"{github_url}/issues"}

setup(
    name="pyfreenas",
    version=version,
    author="Shawn Wilsher",
    author_email="me@shawnwilsher.com",
    packages=["pyfreenas"],
    install_requires=["websockets==8.1", "meteor-ejson==1.1.0"],
    url=github_url,
    download_url=download_url,
    project_urls=project_urls,
    license="MIT",
    description="A Python module for the FreeNAS websocket API.",
    platforms="Cross Platform",
    python_requires=">3.8, <4",
)