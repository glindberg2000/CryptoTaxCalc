#!/usr/bin/env python3
"""
Setup script for CryptoTaxCalc
"""

from setuptools import setup, find_packages
import os


# Read the README file for long description
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()


# Read requirements from requirements.txt
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        return [
            line.strip() for line in fh if line.strip() and not line.startswith("#")
        ]


setup(
    name="cryptotaxcalc",
    version="0.1.0",
    author="CryptoTaxCalc Team",
    author_email="contact@cryptotaxcalc.com",
    description="Automated cryptocurrency tax calculations with IRS compliance",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/glindberg2000/CryptoTaxCalc",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Financial and Insurance Industry",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.12",
        "Topic :: Office/Business :: Financial :: Accounting",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.12",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.5.0",
        ],
        "docs": [
            "sphinx>=7.0.0",
            "sphinx-rtd-theme>=1.3.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "cryptotaxcalc=cryptotaxcalc.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "cryptotaxcalc": ["data/*.csv", "data/*.json", "templates/*"],
    },
    keywords="cryptocurrency, tax, fifo, capital gains, irs, defi",
    project_urls={
        "Bug Reports": "https://github.com/glindberg2000/CryptoTaxCalc/issues",
        "Source": "https://github.com/glindberg2000/CryptoTaxCalc",
        "Documentation": "https://github.com/glindberg2000/CryptoTaxCalc/tree/main/docs",
    },
)
