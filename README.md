# Gantt Pro

Professional Gantt Chart Analysis and Management System for Python.

## Features

- **Excel Import/Export**: Load and save Gantt charts from Excel files
- **Interactive Visualization**: Beautiful Plotly-based Gantt charts
- **Web Dashboard**: Full-featured Dash dashboard for project management
- **REST API**: Flask-based API for integration with other systems
- **CLI Interface**: Powerful command-line tools with Rich formatting
- **Task Management**: Create, update, delete, and search tasks
- **Progress Tracking**: Monitor project and task progress
- **Analytics**: Category breakdowns, owner workload, timeline heatmaps

## Installation

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install package
pip install -e .
```

## Quick Start

### Python API

```python
from gantt_pro import GanttManager, GanttVisualizer

# Load Gantt chart
manager = GanttManager("Gantt chart.xlsx")

# Get project info
print(manager.project.summary())

# Get statistics
stats = manager.get_statistics()
print(f"Total tasks: {stats['total_tasks']}")
print(f"Overall progress: {stats['overall_progress']}%")

# Create visualization
visualizer = GanttVisualizer(manager.project)
visualizer.show()  # Opens in browser

# Export
manager.export_excel("output.xlsx")
manager.export_csv("output.csv")
```

### CLI Commands

```bash
# Show project info
gantt info "Gantt chart.xlsx"

# List tasks
gantt tasks "Gantt chart.xlsx"
gantt tasks "Gantt chart.xlsx" --category SEO
gantt tasks "Gantt chart.xlsx" --owner George
gantt tasks "Gantt chart.xlsx" --overdue

# Show progress
gantt progress "Gantt chart.xlsx"

# Show task tree
gantt tree "Gantt chart.xlsx"

# Search tasks
gantt search "Gantt chart.xlsx" "SEO"

# Export
gantt export "Gantt chart.xlsx" -f excel -o output
gantt export "Gantt chart.xlsx" -f csv
gantt export "Gantt chart.xlsx" -f json
gantt export "Gantt chart.xlsx" -f html

# Generate chart
gantt chart "Gantt chart.xlsx"  # Opens in browser
gantt chart "Gantt chart.xlsx" -o chart.html

# Launch dashboard
gantt dashboard "Gantt chart.xlsx"

# Launch API server
gantt api "Gantt chart.xlsx"
```

### Web Dashboard

```python
from gantt_pro.visualization.dashboard import run_dashboard

# Start interactive dashboard
run_dashboard("Gantt chart.xlsx", port=8050)
```

Then open http://localhost:8050 in your browser.

### REST API

```python
from gantt_pro.api.routes import run_api
from gantt_pro.core.manager import GanttManager

manager = GanttManager("Gantt chart.xlsx")
run_api(manager, port=5000)
```

API Endpoints:
- `GET /api/project` - Get project info
- `GET /api/tasks` - List all tasks
- `GET /api/tasks/<id>` - Get specific task
- `POST /api/tasks` - Create task
- `PUT /api/tasks/<id>` - Update task
- `DELETE /api/tasks/<id>` - Delete task
- `GET /api/statistics` - Get project statistics
- `GET /api/export/excel` - Download Excel export
- `GET /api/chart/html` - Get interactive chart HTML

## Project Structure

```
gantt_pro/
├── __init__.py          # Package exports
├── cli.py               # CLI interface (Typer + Rich)
├── core/
│   ├── models.py        # Data models (Task, Project, Resource)
│   ├── parser.py        # Excel file parser
│   └── manager.py       # Core operations manager
├── visualization/
│   ├── charts.py        # Plotly visualizations
│   └── dashboard.py     # Dash web dashboard
├── api/
│   └── routes.py        # Flask REST API
└── utils/
    └── helpers.py       # Utility functions
```

## Data Models

### Task
- `id`: Unique identifier
- `wbs`: Work Breakdown Structure number
- `name`: Task name
- `category`: Task category/phase
- `start_date`: Start date
- `end_date`: Due date
- `duration`: Duration in days
- `progress`: Completion percentage (0-100)
- `owner`: Assigned resource
- `status`: NOT_STARTED, IN_PROGRESS, COMPLETED, ON_HOLD, CANCELLED
- `priority`: LOW, MEDIUM, HIGH, CRITICAL

### Project
- `name`: Project name
- `manager`: Project manager
- `company`: Company name
- `tasks`: List of tasks
- `phases`: List of phases

## License

MIT License
