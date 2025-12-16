"""
Gantt Chart Manager - Core operations for managing Gantt charts.
"""

import pandas as pd
from datetime import date, timedelta
from typing import Optional, List, Dict, Any, Callable
from pathlib import Path
import json

from gantt_pro.core.models import Task, Project, Phase, Resource, TaskStatus, Priority
from gantt_pro.core.parser import GanttParser


class GanttManager:
    """Manager for Gantt chart operations."""

    def __init__(self, file_path: Optional[str] = None):
        """Initialize manager with optional file path."""
        self.project: Optional[Project] = None
        self.file_path: Optional[Path] = None
        self._history: List[Dict[str, Any]] = []
        self._undo_stack: List[Project] = []

        if file_path:
            self.load(file_path)

    def load(self, file_path: str) -> Project:
        """Load a Gantt chart from an Excel file."""
        self.file_path = Path(file_path)
        parser = GanttParser(file_path)
        self.project = parser.parse()
        self._save_state("load")
        return self.project

    def _save_state(self, action: str) -> None:
        """Save current state for undo functionality."""
        if self.project:
            import copy
            self._undo_stack.append(copy.deepcopy(self.project))
            if len(self._undo_stack) > 50:
                self._undo_stack.pop(0)
            self._history.append({
                "action": action,
                "timestamp": date.today().isoformat()
            })

    def undo(self) -> bool:
        """Undo last operation."""
        if len(self._undo_stack) > 1:
            self._undo_stack.pop()
            self.project = self._undo_stack[-1]
            return True
        return False

    def new_project(self, name: str, manager: Optional[str] = None,
                    company: Optional[str] = None) -> Project:
        """Create a new empty project."""
        self.project = Project(
            name=name,
            manager=manager,
            company=company
        )
        self._save_state("new_project")
        return self.project

    # Task Operations
    def add_task(self, name: str, start_date: Optional[date] = None,
                 end_date: Optional[date] = None, duration: int = 0,
                 owner: Optional[str] = None, category: Optional[str] = None,
                 **kwargs) -> Task:
        """Add a new task to the project."""
        if not self.project:
            raise ValueError("No project loaded")

        task = Task(
            name=name,
            start_date=start_date,
            end_date=end_date,
            duration=duration,
            owner=owner,
            category=category,
            **kwargs
        )

        self.project.add_task(task)
        self._save_state(f"add_task:{name}")
        return task

    def update_task(self, task_id: str, **updates) -> Optional[Task]:
        """Update a task by ID."""
        if not self.project:
            return None

        task = self.project.get_task(task_id)
        if not task:
            return None

        for key, value in updates.items():
            if hasattr(task, key):
                setattr(task, key, value)

        self._save_state(f"update_task:{task_id}")
        return task

    def delete_task(self, task_id: str) -> bool:
        """Delete a task by ID."""
        if not self.project:
            return False

        result = self.project.remove_task(task_id)
        if result:
            self._save_state(f"delete_task:{task_id}")
        return result

    def update_progress(self, task_id: str, progress: float) -> Optional[Task]:
        """Update task progress."""
        return self.update_task(task_id, progress=progress)

    def bulk_update_progress(self, updates: Dict[str, float]) -> int:
        """Update progress for multiple tasks."""
        count = 0
        for task_id, progress in updates.items():
            if self.update_progress(task_id, progress):
                count += 1
        return count

    def set_task_dates(self, task_id: str, start_date: date,
                       end_date: date) -> Optional[Task]:
        """Set task start and end dates."""
        return self.update_task(task_id, start_date=start_date, end_date=end_date)

    def shift_task(self, task_id: str, days: int) -> Optional[Task]:
        """Shift a task by number of days."""
        if not self.project:
            return None

        task = self.project.get_task(task_id)
        if not task or not task.start_date:
            return None

        new_start = task.start_date + timedelta(days=days)
        new_end = task.end_date + timedelta(days=days) if task.end_date else None

        return self.update_task(task_id, start_date=new_start, end_date=new_end)

    def shift_all_tasks(self, days: int) -> int:
        """Shift all tasks by number of days."""
        if not self.project:
            return 0

        count = 0
        for task in self.project.all_tasks:
            if self.shift_task(task.id, days):
                count += 1
        return count

    # Filtering and Querying
    def filter_tasks(self, predicate: Callable[[Task], bool]) -> List[Task]:
        """Filter tasks using a predicate function."""
        if not self.project:
            return []
        return [t for t in self.project.all_tasks if predicate(t)]

    def get_tasks_by_date_range(self, start: date, end: date) -> List[Task]:
        """Get tasks within a date range."""
        def in_range(t: Task) -> bool:
            if not t.start_date or not t.end_date:
                return False
            return t.start_date <= end and t.end_date >= start
        return self.filter_tasks(in_range)

    def get_tasks_by_status(self, status: TaskStatus) -> List[Task]:
        """Get tasks by status."""
        return self.filter_tasks(lambda t: t.status == status)

    def get_tasks_by_owner(self, owner: str) -> List[Task]:
        """Get tasks assigned to an owner."""
        return self.filter_tasks(lambda t: t.owner == owner)

    def get_tasks_by_category(self, category: str) -> List[Task]:
        """Get tasks in a category."""
        return self.filter_tasks(lambda t: t.category == category)

    def search_tasks(self, query: str) -> List[Task]:
        """Search tasks by name."""
        query_lower = query.lower()
        return self.filter_tasks(lambda t: query_lower in t.name.lower())

    # Analytics
    def get_statistics(self) -> Dict[str, Any]:
        """Get project statistics."""
        if not self.project:
            return {}

        tasks = self.project.all_tasks
        return {
            "total_tasks": len(tasks),
            "completed": sum(1 for t in tasks if t.status == TaskStatus.COMPLETED),
            "in_progress": sum(1 for t in tasks if t.status == TaskStatus.IN_PROGRESS),
            "not_started": sum(1 for t in tasks if t.status == TaskStatus.NOT_STARTED),
            "overdue": len(self.project.get_overdue_tasks()),
            "overall_progress": round(self.project.overall_progress, 2),
            "total_cost": self.project.total_cost,
            "project_duration": self.project.project_duration,
            "categories": self.get_category_breakdown(),
            "owner_workload": self.get_owner_workload(),
        }

    def get_category_breakdown(self) -> Dict[str, Dict[str, Any]]:
        """Get breakdown by category."""
        if not self.project:
            return {}

        breakdown = {}
        for task in self.project.all_tasks:
            cat = task.category or "Uncategorized"
            if cat not in breakdown:
                breakdown[cat] = {
                    "count": 0,
                    "completed": 0,
                    "total_duration": 0,
                    "avg_progress": 0,
                }
            breakdown[cat]["count"] += 1
            breakdown[cat]["total_duration"] += task.duration
            breakdown[cat]["avg_progress"] += task.progress
            if task.status == TaskStatus.COMPLETED:
                breakdown[cat]["completed"] += 1

        for cat in breakdown:
            count = breakdown[cat]["count"]
            if count > 0:
                breakdown[cat]["avg_progress"] = round(
                    breakdown[cat]["avg_progress"] / count, 2
                )

        return breakdown

    def get_owner_workload(self) -> Dict[str, Dict[str, Any]]:
        """Get workload breakdown by owner."""
        if not self.project:
            return {}

        workload = {}
        for task in self.project.all_tasks:
            owner = task.owner or "Unassigned"
            if owner not in workload:
                workload[owner] = {
                    "task_count": 0,
                    "total_duration": 0,
                    "completed": 0,
                    "in_progress": 0,
                }
            workload[owner]["task_count"] += 1
            workload[owner]["total_duration"] += task.duration
            if task.status == TaskStatus.COMPLETED:
                workload[owner]["completed"] += 1
            elif task.status == TaskStatus.IN_PROGRESS:
                workload[owner]["in_progress"] += 1

        return workload

    def get_timeline_data(self) -> List[Dict[str, Any]]:
        """Get data formatted for timeline visualization."""
        if not self.project:
            return []

        data = []
        for task in self.project.all_tasks:
            if task.start_date and task.end_date:
                data.append({
                    "id": task.id,
                    "name": task.name,
                    "category": task.category or "General",
                    "start": task.start_date.isoformat(),
                    "end": task.end_date.isoformat(),
                    "progress": task.progress,
                    "owner": task.owner,
                    "status": task.status.value,
                    "duration": task.duration,
                })
        return data

    # Export Functions
    def to_dataframe(self) -> pd.DataFrame:
        """Convert project to pandas DataFrame."""
        if not self.project:
            return pd.DataFrame()

        records = []
        for task in self.project.all_tasks:
            records.append({
                "ID": task.id,
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
                "Priority": task.priority.name,
                "Is Overdue": task.is_overdue,
            })

        return pd.DataFrame(records)

    def export_excel(self, output_path: str, include_charts: bool = True) -> str:
        """Export project to Excel file."""
        df = self.to_dataframe()

        with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Tasks', index=False)

            # Add summary sheet
            summary_data = self.get_statistics()
            summary_df = pd.DataFrame([
                {"Metric": k, "Value": str(v)}
                for k, v in summary_data.items()
                if not isinstance(v, dict)
            ])
            summary_df.to_excel(writer, sheet_name='Summary', index=False)

            # Format the workbook
            workbook = writer.book
            worksheet = writer.sheets['Tasks']

            # Add conditional formatting for progress
            worksheet.conditional_format('H2:H1000', {
                'type': '3_color_scale',
                'min_color': '#FF6B6B',
                'mid_color': '#FFE66D',
                'max_color': '#4ECDC4'
            })

        return output_path

    def export_csv(self, output_path: str) -> str:
        """Export project to CSV file."""
        df = self.to_dataframe()
        df.to_csv(output_path, index=False)
        return output_path

    def export_json(self, output_path: str) -> str:
        """Export project to JSON file."""
        if not self.project:
            return ""

        data = self.project.to_dict()
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        return output_path

    def save(self, output_path: Optional[str] = None) -> str:
        """Save project to Excel file."""
        if output_path is None:
            if self.file_path:
                output_path = str(self.file_path.with_suffix('.gantt.xlsx'))
            else:
                output_path = "project.xlsx"
        return self.export_excel(output_path)

    # Batch Operations
    def complete_tasks_by_category(self, category: str) -> int:
        """Mark all tasks in a category as completed."""
        count = 0
        for task in self.get_tasks_by_category(category):
            if self.update_task(task.id, progress=100):
                count += 1
        return count

    def assign_category_to_owner(self, category: str, owner: str) -> int:
        """Assign all tasks in a category to an owner."""
        count = 0
        for task in self.get_tasks_by_category(category):
            if self.update_task(task.id, owner=owner):
                count += 1
        return count

    def reschedule_overdue(self, days_offset: int = 0) -> int:
        """Reschedule all overdue tasks to start today."""
        today = date.today() + timedelta(days=days_offset)
        count = 0

        for task in self.project.get_overdue_tasks():
            if task.duration > 0:
                new_end = today + timedelta(days=task.duration)
                if self.update_task(task.id, start_date=today, end_date=new_end):
                    count += 1

        return count
