from setuptools import setup, find_packages

VERSION = '0.0.17'
DESCRIPTION = "Automate Stanford's GREAT browser"
LONG_DESCRIPTION = "A Selenium implementation in Python for Stanford's GREAT browser, allowing for quick and easy genomic analysis."

setup(
    name="greatbrowser",
    version=VERSION,
    author="Sam Anderson",
    author_email="sanderson01@wesleyan.edu",
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    url="https://github.com/SamAndTheSun/greatbrowser",  # URL to your package's repository
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

