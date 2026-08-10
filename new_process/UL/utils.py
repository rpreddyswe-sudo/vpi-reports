"""
Utility functions for VPI DL Monthly Report
"""

from datetime import datetime

def add_months(dt, months):
    """Add months to a datetime object (simple implementation)"""
    year = dt.year + (dt.month + months - 1) // 12
    month = (dt.month + months - 1) % 12 + 1
    return dt.replace(year=year, month=month)