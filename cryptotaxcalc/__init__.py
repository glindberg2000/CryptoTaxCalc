"""
CryptoTaxCalc - Automated cryptocurrency tax calculations with IRS compliance.

A Python-based application for processing cryptocurrency transaction data,
applying FIFO lot matching, and generating IRS-compliant tax reports.
"""

__version__ = "0.1.0"
__author__ = "CryptoTaxCalc Team"
__email__ = "contact@cryptotaxcalc.com"

# Core modules
from . import parser
from . import fifo_manager
from . import fmv_fetcher
from . import tax_calculator
from . import reporter
from . import database
from . import utils

# Public API
__all__ = [
    "parser",
    "fifo_manager",
    "fmv_fetcher",
    "tax_calculator",
    "reporter",
    "database",
    "utils",
]
