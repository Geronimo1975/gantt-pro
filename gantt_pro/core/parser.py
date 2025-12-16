"""
Parser for Gantt Chart Excel files.
"""

import pandas as pd
from datetime import datetime, date
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path

from gantt_pro.core.models import Task, Project, Phase, Resource, TaskStatus


class GanttParser:
    """Parser for Excel Gantt chart files."""

    # Common column name patterns
    COLUMN_PATTERNS = {
        "wbs": ["wbs", "wbs number", "wbs_number", "id", "task id", "task_id"],
        "name": ["task", "task title", "task_title", "name", "title", "task name", "activity"],
        "category": ["category", "phase", "group", "type", "section"],
        "start_date": ["start", "start date", "start_date", "begin", "begin date"],
        "end_date": ["end", "end date", "end_date", "due", "due date", "finish", "finish date"],
        "duration": ["duration", "days", "length", "span"],
        "progress": ["progress", "pct", "percent", "completion", "% complete", "pct of task complete"],
        "owner": ["owner", "assignee", "assigned", "resource", "task owner", "responsible"],
        "cost": ["cost", "budget", "monthly cost", "monthly_cost", "price"],
        "status": ["status", "state"],
        "notes": ["notes", "comments", "description", "remarks"],
    }

    def __init__(self, file_path: str):
        """Initialize parser with file path."""
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        self.sheets: Dict[str, pd.DataFrame] = {}
        self._load_file()

    def _load_file(self) -> None:
        """Load Excel file into memory."""
        self.sheets = pd.read_excel(self.file_path, sheet_name=None)

    def _find_column(self, df: pd.DataFrame, field: str) -> Optional[str]:
        """Find column matching a field pattern."""
        patterns = self.COLUMN_PATTERNS.get(field, [field])
        columns_lower = {str(c).lower().strip(): c for c in df.columns}

        for pattern in patterns:
            if pattern.lower() in columns_lower:
                return columns_lower[pattern.lower()]

        # Fuzzy match
        for pattern in patterns:
            for col_lower, col_orig in columns_lower.items():
                if pattern.lower() in col_lower:
                    return col_orig

        return None

    def _parse_date(self, value: Any) -> Optional[date]:
        """Parse date from various formats."""
        if pd.isna(value):
            return None
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        if isinstance(value, str):
            for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y"]:
                try:
                    return datetime.strptime(value, fmt).date()
                except ValueError:
                    continue
        return None

    def _parse_number(self, value: Any, default: float = 0.0) -> float:
        """Parse number from various formats."""
        if pd.isna(value):
            return default
        try:
            return float(value)
        except (ValueError, TypeError):
            return default

    def get_sheet_names(self) -> List[str]:
        """Get list of sheet names."""
        return list(self.sheets.keys())

    def parse_task_management_sheet(self, sheet_name: str = "Task Managemnt") -> List[Task]:
        """Parse the Task Management sheet format."""
        if sheet_name not in self.sheets:
            return []

        df = self.sheets[sheet_name]
        tasks = []

        for idx, row in df.iterrows():
            values = row.values

            # Skip header row or empty rows
            if pd.isna(values[0]) or not str(values[0]).strip():
                continue

            task = Task(
                name=str(values[0]).strip() if not pd.isna(values[0]) else "",
                category=str(values[1]).strip() if len(values) > 1 and not pd.isna(values[1]) else None,
                start_date=self._parse_date(values[2]) if len(values) > 2 else None,
                duration=int(self._parse_number(values[3])) if len(values) > 3 else 0,
                end_date=self._parse_date(values[4]) if len(values) > 4 else None,
            )

            if task.name:
                tasks.append(task)

        return tasks

    def parse_gantt_chart_sheet(self, sheet_name: str = "Gantt Chart") -> Tuple[Project, List[Task]]:
        """Parse the main Gantt Chart sheet."""
        if sheet_name not in self.sheets:
            raise ValueError(f"Sheet '{sheet_name}' not found")

        df = self.sheets[sheet_name]
        project = Project()
        tasks = []

        # Extract project metadata from header rows
        for idx, row in df.iterrows():
            row_str = " ".join(str(v) for v in row.values if not pd.isna(v))

            if "PROJECT TITLE" in row_str.upper():
                # Find project title value
                for i, v in enumerate(row.values):
                    if not pd.isna(v) and str(v).strip() not in ["PROJECT TITLE", ""]:
                        project.name = str(v).strip()
                        break

            if "PROJECT MANAGER" in row_str.upper():
                for i, v in enumerate(row.values):
                    if not pd.isna(v) and str(v).strip() not in ["PROJECT MANAGER", ""]:
                        project.manager = str(v).strip()
                        break

            if "COMPANY NAME" in row_str.upper():
                for i, v in enumerate(row.values):
                    if not pd.isna(v) and str(v).strip() not in ["COMPANY NAME", ""]:
                        project.company = str(v).strip()
                        break

            if "DATE" in row_str.upper() and "START" not in row_str.upper():
                for i, v in enumerate(row.values):
                    d = self._parse_date(v)
                    if d:
                        project.created_date = d
                        break

            # Find header row (contains WBS NUMBER and TASK TITLE)
            if "WBS NUMBER" in row_str.upper() or "TASK TITLE" in row_str.upper():
                # Found header - now parse tasks
                col_map = {}
                for i, v in enumerate(row.values):
                    if pd.isna(v):
                        continue
                    v_str = str(v).strip().upper()
                    if "WBS" in v_str:
                        col_map["wbs"] = i
                    elif "TASK" in v_str and "TITLE" in v_str:
                        col_map["name"] = i
                    elif "START" in v_str and "DATE" in v_str:
                        col_map["start_date"] = i
                    elif "DUE" in v_str or ("END" in v_str and "DATE" in v_str):
                        col_map["end_date"] = i
                    elif "DURATION" in v_str:
                        col_map["duration"] = i
                    elif "PCT" in v_str or "COMPLETE" in v_str:
                        col_map["progress"] = i
                    elif "OWNER" in v_str:
                        col_map["owner"] = i
                    elif "COST" in v_str:
                        col_map["cost"] = i

                # Also check column 2 for category names (like SEO, Email marketing)
                col_map["category"] = 2

                # Parse remaining rows as tasks
                continue

        # Now parse tasks from the detected structure
        # Based on the file structure: column 1 = WBS, column 2 = category, column 3 = task name
        current_category = None
        parent_task = None

        for idx, row in df.iterrows():
            values = row.values

            # Skip first rows (headers)
            if idx < 6:
                continue

            wbs = str(values[1]).strip() if len(values) > 1 and not pd.isna(values[1]) else ""
            category = str(values[2]).strip() if len(values) > 2 and not pd.isna(values[2]) else ""
            task_name = str(values[3]).strip() if len(values) > 3 and not pd.isna(values[3]) else ""

            # Skip empty rows
            if not wbs and not task_name and not category:
                continue

            # If category is present but no task name, this is a category header
            if category and not task_name and not wbs.count(".") > 1:
                current_category = category
                continue

            # Use task_name or category as the actual name
            name = task_name if task_name else category

            if not name or name == "nan":
                continue

            task = Task(
                wbs=wbs,
                name=name,
                category=current_category,
                owner=str(values[5]).strip() if len(values) > 5 and not pd.isna(values[5]) else None,
                start_date=self._parse_date(values[6]) if len(values) > 6 else None,
                end_date=self._parse_date(values[7]) if len(values) > 7 else None,
                duration=int(self._parse_number(values[8])) if len(values) > 8 else 0,
                progress=self._parse_number(values[9]) if len(values) > 9 else 0.0,
                cost=self._parse_number(values[4]) if len(values) > 4 else 0.0,
            )

            # Determine parent-child relationships based on WBS
            if wbs:
                parts = wbs.split(".")
                if len(parts) == 1:
                    # Top-level task group
                    parent_task = task
                    tasks.append(task)
                elif len(parts) == 2:
                    # Category task
                    current_category = name
                    parent_task = task
                    tasks.append(task)
                else:
                    # Subtask
                    task.category = current_category
                    if parent_task:
                        task.parent_id = parent_task.id
                    tasks.append(task)
            else:
                tasks.append(task)

        project.tasks = tasks
        return project, tasks

    def parse(self) -> Project:
        """Parse the entire Excel file and return a Project."""
        project = Project()
        all_tasks = []

        # Try to parse main Gantt Chart sheet
        if "Gantt Chart" in self.sheets:
            project, tasks = self.parse_gantt_chart_sheet("Gantt Chart")
            all_tasks.extend(tasks)

        # Also parse Task Management sheet for additional/cleaner data
        if "Task Managemnt" in self.sheets:
            task_mgmt_tasks = self.parse_task_management_sheet("Task Managemnt")
            # Merge or replace tasks with cleaner data
            if task_mgmt_tasks and not all_tasks:
                all_tasks = task_mgmt_tasks

        # Update project with tasks
        if not project.tasks:
            project.tasks = all_tasks

        # Set project dates from tasks
        start_dates = [t.start_date for t in project.tasks if t.start_date]
        end_dates = [t.end_date for t in project.tasks if t.end_date]

        if start_dates:
            project.start_date = min(start_dates)
        if end_dates:
            project.end_date = max(end_dates)

        return project

    def get_raw_data(self, sheet_name: Optional[str] = None) -> pd.DataFrame:
        """Get raw DataFrame for a sheet."""
        if sheet_name:
            return self.sheets.get(sheet_name, pd.DataFrame())
        # Return first sheet
        return next(iter(self.sheets.values()), pd.DataFrame())

    def to_clean_dataframe(self) -> pd.DataFrame:
        """Convert parsed tasks to a clean DataFrame."""
        project = self.parse()
        records = []

        for task in project.all_tasks:
            records.append({
                "WBS": task.wbs,
                "Task Name": task.name,
                "Category": task.category,
                "Owner": task.owner,
                "Start Date": task.start_date,
                "End Date": task.end_date,
                "Duration (days)": task.duration,
                "Progress (%)": task.progress,
                "Status": task.status.value,
                "Cost": task.cost,
            })

        return pd.DataFrame(records)
