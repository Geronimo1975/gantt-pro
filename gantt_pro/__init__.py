"""
Gantt Pro - Professional Gantt Chart Analysis and Management System
=====================================================================

A comprehensive Python library for analyzing, editing, and visualizing
Gantt charts with professional-grade features.

Features:
- Load and parse Excel Gantt charts
- Interactive visualization with Plotly
- Web-based dashboard with Dash
- CLI interface for quick operations
- Export to multiple formats (Excel, CSV, PNG, HTML, PDF)
- Critical path analysis
- Resource management
- Progress tracking
"""

__version__ = "1.0.0"
__author__ = "George Sebastian Cucuiet"

from gantt_pro.core.models import Task, Project, Resource
from gantt_pro.core.parser import GanttParser
from gantt_pro.core.manager import GanttManager
from gantt_pro.visualization.charts import GanttVisualizer

__all__ = [
    "Task",
    "Project",
    "Resource",
    "GanttParser",
    "GanttManager",
    "GanttVisualizer",
]
