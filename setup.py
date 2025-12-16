"""
Setup configuration for Gantt Pro.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="gantt-pro",
    version="1.0.0",
    author="George Sebastian Cucuiet",
    author_email="george@example.com",
    description="Professional Gantt Chart Analysis and Management System",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/george/gantt-pro",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Office/Business :: Scheduling",
    ],
    python_requires=">=3.10",
    install_requires=[
        "pandas>=2.0.0",
        "openpyxl>=3.1.0",
        "xlsxwriter>=3.1.0",
        "python-dateutil>=2.8.0",
        "plotly>=5.18.0",
        "dash>=2.14.0",
        "dash-bootstrap-components>=1.5.0",
        "typer>=0.9.0",
        "rich>=13.7.0",
    ],
    extras_require={
        "api": ["flask>=3.0.0"],
        "export": ["kaleido>=0.2.1"],
        "full": ["flask>=3.0.0", "kaleido>=0.2.1"],
    },
    entry_points={
        "console_scripts": [
            "gantt=gantt_pro.cli:main",
            "gantt-pro=gantt_pro.cli:main",
        ],
    },
)
