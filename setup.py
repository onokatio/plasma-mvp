# -*- coding: utf-8 -*-
from setuptools import find_packages
from setuptools import setup

with open("README.md") as f:
    readme = f.read()

setup(
    name="plasma",
    description="Plasma MVP",
    long_description=readme,
    author="David Knott",
    author_email="",
    license=license,
    packages=find_packages(exclude=("tests")),
    include_package_data=True,
    install_requires=[
        "ethereum==2.3.0",
        "web3==5.13.1",
        "werkzeug==0.14.1",
        "json-rpc==1.10.8",
        "py-solc",
        "pytest-cov",
        "click==6.7",
        "flake8==3.5.0",
        "rlp==0.6.0",
    ],
    entry_points={
        "console_scripts": ["omg=plasma.cli:cli"],
    },
)
