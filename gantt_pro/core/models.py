"""
Data models for Gantt Chart management.
"""

from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from enum import Enum
from typing import Optional, List, Dict, Any
import uuid


class TaskStatus(Enum):
    """Task completion status."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ON_HOLD = "on_hold"
    CANCELLED = "cancelled"


class Priority(Enum):
    """Task priority levels."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class Resource:
    """Represents a team member or resource."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    email: Optional[str] = None
    role: Optional[str] = None
    hourly_rate: float = 0.0
    availability: float = 1.0  # 0.0 to 1.0

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())[:8]


@dataclass
class Task:
    """Represents a single task in the Gantt chart."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    wbs: str = ""  # Work Breakdown Structure number
    name: str = ""
    description: Optional[str] = None
    category: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    duration: int = 0  # in days
    progress: float = 0.0  # 0.0 to 100.0
    status: TaskStatus = TaskStatus.NOT_STARTED
    priority: Priority = Priority.MEDIUM
    owner: Optional[str] = None
    cost: float = 0.0
    parent_id: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    subtasks: List['Task'] = field(default_factory=list)
    resources: List[Resource] = field(default_factory=list)
    notes: Optional[str] = None
    color: Optional[str] = None

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())[:8]

        # Calculate duration if dates are set
        if self.start_date and self.end_date and self.duration == 0:
            self.duration = (self.end_date - self.start_date).days

        # Calculate end date if start and duration are set
        elif self.start_date and self.duration > 0 and not self.end_date:
            self.end_date = self.start_date + timedelta(days=self.duration)

        # Update status based on progress
        if self.progress >= 100:
            self.status = TaskStatus.COMPLETED
        elif self.progress > 0:
            self.status = TaskStatus.IN_PROGRESS

    @property
    def is_milestone(self) -> bool:
        """Check if task is a milestone (zero duration)."""
        return self.duration == 0 and self.start_date == self.end_date

    @property
    def is_overdue(self) -> bool:
        """Check if task is overdue."""
        if not self.end_date:
            return False
        return date.today() > self.end_date and self.progress < 100

    @property
    def days_remaining(self) -> int:
        """Get days remaining until due date."""
        if not self.end_date:
            return 0
        remaining = (self.end_date - date.today()).days
        return max(0, remaining)

    @property
    def is_parent(self) -> bool:
        """Check if task has subtasks."""
        return len(self.subtasks) > 0

    def add_subtask(self, task: 'Task') -> None:
        """Add a subtask."""
        task.parent_id = self.id
        self.subtasks.append(task)

    def update_progress(self, progress: float) -> None:
        """Update task progress."""
        self.progress = max(0, min(100, progress))
        if self.progress >= 100:
            self.status = TaskStatus.COMPLETED
        elif self.progress > 0:
            self.status = TaskStatus.IN_PROGRESS
        else:
            self.status = TaskStatus.NOT_STARTED

    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary."""
        return {
            "id": self.id,
            "wbs": self.wbs,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "duration": self.duration,
            "progress": self.progress,
            "status": self.status.value,
            "priority": self.priority.value,
            "owner": self.owner,
            "cost": self.cost,
            "parent_id": self.parent_id,
            "dependencies": self.dependencies,
            "notes": self.notes,
            "color": self.color,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """Create task from dictionary."""
        if data.get("start_date") and isinstance(data["start_date"], str):
            data["start_date"] = date.fromisoformat(data["start_date"])
        if data.get("end_date") and isinstance(data["end_date"], str):
            data["end_date"] = date.fromisoformat(data["end_date"])
        if data.get("status"):
            data["status"] = TaskStatus(data["status"])
        if data.get("priority"):
            data["priority"] = Priority(data["priority"])
        return cls(**data)


@dataclass
class Phase:
    """Represents a project phase containing multiple tasks."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    description: Optional[str] = None
    tasks: List[Task] = field(default_factory=list)
    color: Optional[str] = None
    order: int = 0

    @property
    def start_date(self) -> Optional[date]:
        """Get earliest start date among tasks."""
        dates = [t.start_date for t in self.tasks if t.start_date]
        return min(dates) if dates else None

    @property
    def end_date(self) -> Optional[date]:
        """Get latest end date among tasks."""
        dates = [t.end_date for t in self.tasks if t.end_date]
        return max(dates) if dates else None

    @property
    def progress(self) -> float:
        """Calculate average progress of all tasks."""
        if not self.tasks:
            return 0.0
        return sum(t.progress for t in self.tasks) / len(self.tasks)

    @property
    def total_cost(self) -> float:
        """Calculate total cost of all tasks."""
        return sum(t.cost for t in self.tasks)


@dataclass
class Project:
    """Represents the entire Gantt chart project."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    description: Optional[str] = None
    manager: Optional[str] = None
    company: Optional[str] = None
    created_date: date = field(default_factory=date.today)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    tasks: List[Task] = field(default_factory=list)
    phases: List[Phase] = field(default_factory=list)
    resources: List[Resource] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())[:8]

    @property
    def all_tasks(self) -> List[Task]:
        """Get all tasks including subtasks."""
        all_tasks = []
        for task in self.tasks:
            all_tasks.append(task)
            all_tasks.extend(self._get_subtasks_recursive(task))
        return all_tasks

    def _get_subtasks_recursive(self, task: Task) -> List[Task]:
        """Recursively get all subtasks."""
        subtasks = []
        for subtask in task.subtasks:
            subtasks.append(subtask)
            subtasks.extend(self._get_subtasks_recursive(subtask))
        return subtasks

    @property
    def total_tasks(self) -> int:
        """Get total number of tasks."""
        return len(self.all_tasks)

    @property
    def completed_tasks(self) -> int:
        """Get number of completed tasks."""
        return sum(1 for t in self.all_tasks if t.status == TaskStatus.COMPLETED)

    @property
    def overall_progress(self) -> float:
        """Calculate overall project progress."""
        tasks = self.all_tasks
        if not tasks:
            return 0.0
        return sum(t.progress for t in tasks) / len(tasks)

    @property
    def total_cost(self) -> float:
        """Calculate total project cost."""
        return sum(t.cost for t in self.all_tasks)

    @property
    def project_duration(self) -> int:
        """Get total project duration in days."""
        if not self.start_date or not self.end_date:
            dates = [(t.start_date, t.end_date) for t in self.all_tasks
                     if t.start_date and t.end_date]
            if not dates:
                return 0
            start = min(d[0] for d in dates)
            end = max(d[1] for d in dates)
            return (end - start).days
        return (self.end_date - self.start_date).days

    def add_task(self, task: Task) -> None:
        """Add a task to the project."""
        self.tasks.append(task)

    def remove_task(self, task_id: str) -> bool:
        """Remove a task by ID."""
        for i, task in enumerate(self.tasks):
            if task.id == task_id:
                self.tasks.pop(i)
                return True
        return False

    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID."""
        for task in self.all_tasks:
            if task.id == task_id:
                return task
        return None

    def get_tasks_by_owner(self, owner: str) -> List[Task]:
        """Get all tasks assigned to an owner."""
        return [t for t in self.all_tasks if t.owner == owner]

    def get_tasks_by_category(self, category: str) -> List[Task]:
        """Get all tasks in a category."""
        return [t for t in self.all_tasks if t.category == category]

    def get_overdue_tasks(self) -> List[Task]:
        """Get all overdue tasks."""
        return [t for t in self.all_tasks if t.is_overdue]

    def get_critical_path(self) -> List[Task]:
        """Calculate and return critical path tasks."""
        # Simple critical path: tasks with dependencies that form longest path
        # This is a simplified implementation
        tasks_with_deps = [t for t in self.all_tasks if t.dependencies]
        if not tasks_with_deps:
            # If no dependencies, return tasks with longest duration
            return sorted(self.all_tasks, key=lambda t: t.duration, reverse=True)[:5]
        return tasks_with_deps

    def to_dict(self) -> Dict[str, Any]:
        """Convert project to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "manager": self.manager,
            "company": self.company,
            "created_date": self.created_date.isoformat(),
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "tasks": [t.to_dict() for t in self.tasks],
            "metadata": self.metadata,
        }

    def summary(self) -> Dict[str, Any]:
        """Get project summary statistics."""
        tasks = self.all_tasks
        return {
            "name": self.name,
            "manager": self.manager,
            "company": self.company,
            "total_tasks": len(tasks),
            "completed_tasks": self.completed_tasks,
            "in_progress_tasks": sum(1 for t in tasks if t.status == TaskStatus.IN_PROGRESS),
            "overdue_tasks": len(self.get_overdue_tasks()),
            "overall_progress": round(self.overall_progress, 2),
            "total_cost": self.total_cost,
            "project_duration_days": self.project_duration,
            "categories": list(set(t.category for t in tasks if t.category)),
            "owners": list(set(t.owner for t in tasks if t.owner)),
        }
