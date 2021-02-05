# -*- coding: utf-8 -*-

#  Author: Tank Overlord <TankOverLord88@gmail.com>
#
#  License: LGPL-3.0

import setuptools

import chess4fun

with open("README.rst", "r") as fh:
    long_description = fh.read()

with open("requirements.txt") as fh:
    required = fh.read().splitlines()

setuptools.setup(
    name="chess4fun",
    version=chess4fun.__version__,
    author="Tank Overlord",
    author_email="TankOverLord88@gmail.com",
    description="A Python App for Chess",
    license=chess4fun.__license__,
    long_description=long_description,
    long_description_content_type="text/x-rst",
    url="https://github.com/tank-overlord/chess4fun",
    packages=setuptools.find_packages(),
    # https://pypi.org/classifiers/
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)",
        "Operating System :: OS Independent",
    ],
    install_requires=required,
    python_requires='>=3.7',
    include_package_data=True,
)
