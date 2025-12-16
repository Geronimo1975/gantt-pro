"""
Interactive Gantt Chart Visualization using Plotly.
"""

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import date, timedelta
from typing import Optional, List, Dict, Any
import pandas as pd

from gantt_pro.core.models import Project, Task, TaskStatus


class GanttVisualizer:
    """Create interactive Gantt chart visualizations."""

    # Color schemes
    CATEGORY_COLORS = {
        "SEO": "#3498db",
        "Recruitment": "#e74c3c",
        "Website Reconstruction": "#2ecc71",
        "Email marketing": "#9b59b6",
        "Marketing": "#f39c12",
        "Development": "#1abc9c",
        "Design": "#e91e63",
        "Testing": "#00bcd4",
        "General": "#95a5a6",
    }

    STATUS_COLORS = {
        TaskStatus.NOT_STARTED: "#bdc3c7",
        TaskStatus.IN_PROGRESS: "#3498db",
        TaskStatus.COMPLETED: "#27ae60",
        TaskStatus.ON_HOLD: "#f39c12",
        TaskStatus.CANCELLED: "#e74c3c",
    }

    def __init__(self, project: Optional[Project] = None):
        """Initialize visualizer with optional project."""
        self.project = project

    def set_project(self, project: Project) -> None:
        """Set the project to visualize."""
        self.project = project

    def _get_color(self, task: Task) -> str:
        """Get color for a task based on category."""
        if task.color:
            return task.color
        category = task.category or "General"
        return self.CATEGORY_COLORS.get(category, "#95a5a6")

    def _prepare_dataframe(self) -> pd.DataFrame:
        """Prepare DataFrame for Plotly."""
        if not self.project:
            return pd.DataFrame()

        records = []
        for task in self.project.all_tasks:
            if task.start_date and task.end_date:
                records.append({
                    "Task": task.name[:50] + "..." if len(task.name) > 50 else task.name,
                    "Full Name": task.name,
                    "Category": task.category or "General",
                    "Start": task.start_date,
                    "Finish": task.end_date,
                    "Progress": task.progress,
                    "Owner": task.owner or "Unassigned",
                    "Status": task.status.value,
                    "Duration": task.duration,
                    "WBS": task.wbs,
                    "Color": self._get_color(task),
                })

        return pd.DataFrame(records)

    def create_gantt_chart(self, height: int = 800, show_progress: bool = True,
                           color_by: str = "Category") -> go.Figure:
        """Create an interactive Gantt chart."""
        df = self._prepare_dataframe()

        if df.empty:
            fig = go.Figure()
            fig.add_annotation(text="No tasks with dates to display",
                              xref="paper", yref="paper", x=0.5, y=0.5)
            return fig

        # Create figure with Plotly Express
        fig = px.timeline(
            df,
            x_start="Start",
            x_end="Finish",
            y="Task",
            color=color_by,
            hover_data=["Full Name", "Owner", "Progress", "Duration", "Status"],
            color_discrete_map=self.CATEGORY_COLORS,
            title=f"{self.project.name} - Gantt Chart" if self.project else "Gantt Chart",
        )

        # Add progress bars if enabled
        if show_progress:
            for i, row in df.iterrows():
                if row["Progress"] > 0:
                    progress_end = row["Start"] + timedelta(
                        days=row["Duration"] * row["Progress"] / 100
                    )
                    fig.add_shape(
                        type="rect",
                        x0=row["Start"],
                        x1=progress_end,
                        y0=i - 0.3,
                        y1=i + 0.3,
                        fillcolor="rgba(0,0,0,0.2)",
                        line=dict(width=0),
                        layer="above",
                    )

        # Add today line
        today_str = date.today().isoformat()
        fig.add_shape(
            type="line",
            x0=today_str,
            x1=today_str,
            y0=0,
            y1=1,
            yref="paper",
            line=dict(color="red", width=2, dash="dash"),
        )
        fig.add_annotation(
            x=today_str,
            y=1.02,
            yref="paper",
            text="Today",
            showarrow=False,
            font=dict(color="red", size=12),
        )

        # Update layout
        fig.update_layout(
            height=height,
            xaxis_title="Timeline",
            yaxis_title="Tasks",
            showlegend=True,
            legend_title=color_by,
            hovermode="closest",
            xaxis=dict(
                rangeselector=dict(
                    buttons=list([
                        dict(count=7, label="1W", step="day", stepmode="backward"),
                        dict(count=1, label="1M", step="month", stepmode="backward"),
                        dict(count=3, label="3M", step="month", stepmode="backward"),
                        dict(step="all", label="All"),
                    ])
                ),
                rangeslider=dict(visible=True),
                type="date",
            ),
            yaxis=dict(
                autorange="reversed",
                tickfont=dict(size=10),
            ),
        )

        return fig

    def create_progress_chart(self, by: str = "category") -> go.Figure:
        """Create a progress overview chart."""
        if not self.project:
            return go.Figure()

        if by == "category":
            data = {}
            for task in self.project.all_tasks:
                cat = task.category or "General"
                if cat not in data:
                    data[cat] = {"total": 0, "progress_sum": 0}
                data[cat]["total"] += 1
                data[cat]["progress_sum"] += task.progress

            categories = list(data.keys())
            avg_progress = [data[c]["progress_sum"] / data[c]["total"] for c in categories]
            colors = [self.CATEGORY_COLORS.get(c, "#95a5a6") for c in categories]

        else:  # by owner
            data = {}
            for task in self.project.all_tasks:
                owner = task.owner or "Unassigned"
                if owner not in data:
                    data[owner] = {"total": 0, "progress_sum": 0}
                data[owner]["total"] += 1
                data[owner]["progress_sum"] += task.progress

            categories = list(data.keys())
            avg_progress = [data[c]["progress_sum"] / data[c]["total"] for c in categories]
            colors = px.colors.qualitative.Set3[:len(categories)]

        fig = go.Figure(data=[
            go.Bar(
                x=categories,
                y=avg_progress,
                marker_color=colors,
                text=[f"{p:.1f}%" for p in avg_progress],
                textposition='auto',
            )
        ])

        fig.update_layout(
            title=f"Average Progress by {by.title()}",
            xaxis_title=by.title(),
            yaxis_title="Progress (%)",
            yaxis=dict(range=[0, 100]),
            height=400,
        )

        return fig

    def create_status_pie(self) -> go.Figure:
        """Create a pie chart showing task status distribution."""
        if not self.project:
            return go.Figure()

        status_counts = {}
        for task in self.project.all_tasks:
            status = task.status.value
            status_counts[status] = status_counts.get(status, 0) + 1

        labels = list(status_counts.keys())
        values = list(status_counts.values())
        colors = [self.STATUS_COLORS.get(TaskStatus(l), "#95a5a6") for l in labels]

        fig = go.Figure(data=[
            go.Pie(
                labels=labels,
                values=values,
                marker_colors=colors,
                hole=0.4,
                textinfo='label+percent',
            )
        ])

        fig.update_layout(
            title="Task Status Distribution",
            height=400,
        )

        return fig

    def create_timeline_heatmap(self) -> go.Figure:
        """Create a heatmap showing task density over time."""
        if not self.project:
            return go.Figure()

        df = self._prepare_dataframe()
        if df.empty:
            return go.Figure()

        # Get date range
        min_date = df["Start"].min()
        max_date = df["Finish"].max()

        # Create weekly buckets
        weeks = []
        current = min_date
        while current <= max_date:
            weeks.append(current)
            current += timedelta(weeks=1)

        # Count tasks per category per week
        categories = df["Category"].unique()
        heatmap_data = []

        for cat in categories:
            cat_df = df[df["Category"] == cat]
            row = []
            for week_start in weeks:
                week_end = week_start + timedelta(weeks=1)
                count = len(cat_df[
                    (cat_df["Start"] <= week_end) &
                    (cat_df["Finish"] >= week_start)
                ])
                row.append(count)
            heatmap_data.append(row)

        fig = go.Figure(data=go.Heatmap(
            z=heatmap_data,
            x=[w.strftime("%Y-%m-%d") for w in weeks],
            y=list(categories),
            colorscale="Blues",
            hoverongaps=False,
        ))

        fig.update_layout(
            title="Task Density Heatmap (by Week)",
            xaxis_title="Week Starting",
            yaxis_title="Category",
            height=400,
        )

        return fig

    def create_owner_workload(self) -> go.Figure:
        """Create a stacked bar chart showing owner workload."""
        if not self.project:
            return go.Figure()

        # Group tasks by owner and status
        data = {}
        for task in self.project.all_tasks:
            owner = task.owner or "Unassigned"
            status = task.status.value
            if owner not in data:
                data[owner] = {}
            data[owner][status] = data[owner].get(status, 0) + 1

        owners = list(data.keys())
        statuses = list(TaskStatus)

        fig = go.Figure()

        for status in statuses:
            values = [data[o].get(status.value, 0) for o in owners]
            fig.add_trace(go.Bar(
                name=status.value,
                x=owners,
                y=values,
                marker_color=self.STATUS_COLORS.get(status, "#95a5a6"),
            ))

        fig.update_layout(
            barmode='stack',
            title="Workload by Owner",
            xaxis_title="Owner",
            yaxis_title="Number of Tasks",
            height=400,
            legend_title="Status",
        )

        return fig

    def create_dashboard_figures(self) -> Dict[str, go.Figure]:
        """Create all dashboard figures."""
        return {
            "gantt": self.create_gantt_chart(),
            "progress_category": self.create_progress_chart("category"),
            "progress_owner": self.create_progress_chart("owner"),
            "status_pie": self.create_status_pie(),
            "timeline_heatmap": self.create_timeline_heatmap(),
            "owner_workload": self.create_owner_workload(),
        }

    def save_html(self, output_path: str, include_all: bool = False) -> str:
        """Save chart as interactive HTML."""
        fig = self.create_gantt_chart()
        fig.write_html(output_path)
        return output_path

    def save_image(self, output_path: str, format: str = "png",
                   width: int = 1920, height: int = 1080) -> str:
        """Save chart as static image."""
        fig = self.create_gantt_chart(height=height)
        fig.write_image(output_path, format=format, width=width, height=height)
        return output_path

    def show(self) -> None:
        """Display the Gantt chart in browser."""
        fig = self.create_gantt_chart()
        fig.show()
