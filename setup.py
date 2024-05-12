from setuptools import setup, find_packages
import codecs
import os

VERSION = '0.0.5'
DESCRIPTION = "Automate Stanford's GREAT browser"
LONG_DESCRIPTION = "A selenium implementation in python for Stanford's GREAT browser, allowing for quick and easy genomic analysis."

# Setting up
setup(
    name="greatbrowser",
    version=VERSION,
    author="SamAndTheSuhn (Sam Anderson)",
    author_email="sanderson01@wesleyan.edu",
    description=DESCRIPTION,
    long_description_content_type="text/markdown",
    long_description=LONG_DESCRIPTION,
    packages=find_packages(),
    install_requires=['selenium', 'bs4', 'requests', 'webdriver_manager', 'pandas', 'polars', 'numpy', 'Pillow', 'urllib3'],
    keywords=['python', 'genomics', 'genetics', 'greatbrowser', 'great', 'automated', 'analysis'],
    classifiers=["Intended Audience :: Science/Research",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Operating System :: Unit",
        "Operating System :: MacOS",
        "Operating System :: Microsoft :: Windows"]
    )
