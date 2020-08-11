"""pyfreenas setup script."""
import setuptools

version = "0.1.0"

github_username = "sdwilsh"
github_repository = "py-freenas"

github_path = f"{github_username}/{github_repository}"
github_url = f"https://github.com/{github_path}"

download_url = f"{github_url}/archive/{version}.tar.gz"
project_urls = {"Bug Reports": f"{github_url}/issues"}

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pyfreenas",
    version=version,
    author="Shawn Wilsher",
    author_email="me@shawnwilsher.com",
    description="A Python module for the FreeNAS websocket API.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url=github_url,
    packages=setuptools.find_packages(),
    install_requires=["websockets==8.1", "meteor-ejson==1.1.0"],
    download_url=download_url,
    project_urls=project_urls,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.8",
    ],
    python_requires=">3.8, <4",
)
