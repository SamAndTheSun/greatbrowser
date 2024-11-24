from setuptools import setup, find_packages

VERSION = '1.1.6'
DESCRIPTION = "Automate Stanford's GREAT browser"

from pathlib import Path
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name="greatbrowser",
    version=VERSION,
    author="Samuel D. Anderson",
    author_email="sanderson01@wesleyan.edu",
    description=DESCRIPTION,
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=[
        'selenium',
        'beautifulsoup4',
        'requests',
        'webdriver_manager',
        'pandas',
        'polars',
        'numpy',
        'Pillow',
        'urllib3',
        'lxml',
    ],
    keywords=['python', 'genomics', 'genetics', 'greatbrowser', 'great', 'automated', 'analysis'],
    classifiers=[
        "Intended Audience :: Science/Research",
        "Programming Language :: Python :: 3",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: Unix"],
    project_urls={
        'Source': 'https://github.com/SamAndTheSun/greatbrowser',
        'Bug Reports': 'https://github.com/SamAndTheSun/greatbrowser/issues'})

