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
        'selenium==3.141.0',
    ],
)
