"""
Setup file for the kijiji scrapper
"""

from setuptools import setup, find_packages

setup(
    name="kijiji_scrapper",
    python_requires=">=3.9",
    packages=find_packages(where='src', exclude=["tests", "*.tests", "*.tests.*", "tests.*"]),
    package_dir={'': 'src'},
    install_requires=[
        'numpy~=1.21.2',
        'requests~=2.26.0',
        'selenium~=3.141.0',
        'bs4~=0.0.1',
        'beautifulsoup4~=4.9.3',
        'setuptools~=52.0.0',
    ],
)
