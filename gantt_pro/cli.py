"""
Command-Line Interface for Gantt Pro.
"""

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, BarColumn, TextColumn, TaskProgressColumn
from rich.tree import Tree
from rich import print as rprint
from datetime import date
from pathlib import Path
from typing import Optional
import sys

from gantt_pro.core.manager import GanttManager
from gantt_pro.core.models import TaskStatus
from gantt_pro.visualization.charts import GanttVisualizer
from gantt_pro.utils.helpers import format_date, format_duration, progress_bar

app = typer.Typer(
    name="gantt",
    help="Gantt Pro - Professional Gantt Chart Analysis and Management",
    add_completion=True,
)

console = Console()
manager = GanttManager()


def load_project(file_path: str) -> bool:
    """Load project from file."""
    try:
        manager.load(file_path)
        return True
    except Exception as e:
        console.print(f"[red]Error loading file: {e}[/red]")
        return False


@app.command()
def info(file: str = typer.Argument(..., help="Path to Gantt chart Excel file")):
    """Display project information and statistics."""
    if not load_project(file):
        raise typer.Exit(1)

    project = manager.project
    stats = manager.get_statistics()

    # Project info panel
    info_text = f"""
[bold]Project:[/bold] {project.name or 'Unnamed'}
[bold]Manager:[/bold] {project.manager or 'Not specified'}
[bold]Company:[/bold] {project.company or 'Not specified'}
[bold]Created:[/bold] {format_date(project.created_date)}
[bold]Duration:[/bold] {format_duration(stats.get('project_duration', 0))}
"""
    console.print(Panel(info_text, title="Project Information", border_style="blue"))

    # Statistics table
    table = Table(title="Project Statistics", show_header=True, header_style="bold magenta")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right", style="green")

    table.add_row("Total Tasks", str(stats.get("total_tasks", 0)))
    table.add_row("Completed", str(stats.get("completed", 0)))
    table.add_row("In Progress", str(stats.get("in_progress", 0)))
    table.add_row("Not Started", str(stats.get("not_started", 0)))
    table.add_row("Overdue", f"[red]{stats.get('overdue', 0)}[/red]")
    table.add_row("Overall Progress", f"{stats.get('overall_progress', 0):.1f}%")
    table.add_row("Total Cost", f"${stats.get('total_cost', 0):,.2f}")

    console.print(table)

    # Progress bar
    progress = stats.get("overall_progress", 0)
    console.print(f"\n[bold]Overall Progress:[/bold] {progress_bar(progress)}")


@app.command()
def tasks(
    file: str = typer.Argument(..., help="Path to Gantt chart Excel file"),
    category: Optional[str] = typer.Option(None, "--category", "-c", help="Filter by category"),
    owner: Optional[str] = typer.Option(None, "--owner", "-o", help="Filter by owner"),
    status: Optional[str] = typer.Option(None, "--status", "-s", help="Filter by status"),
    overdue: bool = typer.Option(False, "--overdue", help="Show only overdue tasks"),
):
    """List all tasks with optional filters."""
    if not load_project(file):
        raise typer.Exit(1)

    task_list = manager.project.all_tasks

    # Apply filters
    if category:
        task_list = [t for t in task_list if t.category and category.lower() in t.category.lower()]
    if owner:
        task_list = [t for t in task_list if t.owner and owner.lower() in t.owner.lower()]
    if status:
        task_list = [t for t in task_list if t.status.value == status.lower()]
    if overdue:
        task_list = [t for t in task_list if t.is_overdue]

    if not task_list:
        console.print("[yellow]No tasks found matching filters.[/yellow]")
        raise typer.Exit(0)

    # Create table
    table = Table(title=f"Tasks ({len(task_list)} found)", show_header=True, header_style="bold magenta")
    table.add_column("WBS", style="dim", width=8)
    table.add_column("Task", style="cyan", max_width=40)
    table.add_column("Category", style="blue", width=15)
    table.add_column("Owner", style="green", width=12)
    table.add_column("Start", width=12)
    table.add_column("End", width=12)
    table.add_column("Progress", justify="right", width=10)
    table.add_column("Status", width=12)

    for task in task_list:
        status_style = {
            TaskStatus.COMPLETED: "[green]completed[/green]",
            TaskStatus.IN_PROGRESS: "[yellow]in_progress[/yellow]",
            TaskStatus.NOT_STARTED: "[dim]not_started[/dim]",
            TaskStatus.ON_HOLD: "[orange1]on_hold[/orange1]",
            TaskStatus.CANCELLED: "[red]cancelled[/red]",
        }.get(task.status, task.status.value)

        overdue_marker = "[red]*[/red]" if task.is_overdue else ""

        table.add_row(
            task.wbs or "-",
            task.name[:40] + "..." if len(task.name) > 40 else task.name,
            task.category or "-",
            task.owner or "-",
            format_date(task.start_date) or "-",
            format_date(task.end_date) + overdue_marker or "-",
            f"{task.progress:.0f}%",
            status_style,
        )

    console.print(table)


@app.command()
def tree(
    file: str = typer.Argument(..., help="Path to Gantt chart Excel file"),
):
    """Display tasks as a hierarchical tree."""
    if not load_project(file):
        raise typer.Exit(1)

    project = manager.project

    # Build tree
    tree = Tree(f"[bold blue]{project.name or 'Project'}[/bold blue]")

    # Group by category
    categories = {}
    for task in project.all_tasks:
        cat = task.category or "Uncategorized"
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(task)

    for cat_name, cat_tasks in categories.items():
        cat_branch = tree.add(f"[bold magenta]{cat_name}[/bold magenta]")
        for task in cat_tasks:
            status_icon = {
                TaskStatus.COMPLETED: "[green]✓[/green]",
                TaskStatus.IN_PROGRESS: "[yellow]►[/yellow]",
                TaskStatus.NOT_STARTED: "[dim]○[/dim]",
                TaskStatus.ON_HOLD: "[orange1]⏸[/orange1]",
                TaskStatus.CANCELLED: "[red]✗[/red]",
            }.get(task.status, "○")

            task_text = f"{status_icon} {task.name}"
            if task.progress > 0 and task.progress < 100:
                task_text += f" [dim]({task.progress:.0f}%)[/dim]"
            cat_branch.add(task_text)

    console.print(tree)


@app.command()
def progress(
    file: str = typer.Argument(..., help="Path to Gantt chart Excel file"),
):
    """Show progress visualization."""
    if not load_project(file):
        raise typer.Exit(1)

    stats = manager.get_statistics()

    console.print(Panel(
        f"[bold]Project Progress Overview[/bold]\n\n"
        f"Overall: {progress_bar(stats.get('overall_progress', 0), width=40)}",
        title="Progress",
        border_style="green"
    ))

    # Category progress
    console.print("\n[bold]Progress by Category:[/bold]")
    category_breakdown = stats.get("categories", {})
    for cat_name, cat_data in category_breakdown.items():
        avg = cat_data.get("avg_progress", 0)
        console.print(f"  {cat_name:20} {progress_bar(avg, width=30)}")

    # Owner progress
    console.print("\n[bold]Progress by Owner:[/bold]")
    owner_workload = stats.get("owner_workload", {})
    for owner_name, owner_data in owner_workload.items():
        completed = owner_data.get("completed", 0)
        total = owner_data.get("task_count", 0)
        pct = (completed / total * 100) if total > 0 else 0
        console.print(f"  {owner_name:20} {progress_bar(pct, width=30)} ({completed}/{total} tasks)")


@app.command()
def export(
    file: str = typer.Argument(..., help="Path to Gantt chart Excel file"),
    output: str = typer.Option(None, "--output", "-o", help="Output file path"),
    format: str = typer.Option("excel", "--format", "-f", help="Export format: excel, csv, json, html"),
):
    """Export project to various formats."""
    if not load_project(file):
        raise typer.Exit(1)

    # Determine output path
    input_path = Path(file)
    if not output:
        output = str(input_path.parent / f"{input_path.stem}_export")

    with console.status("[bold green]Exporting..."):
        if format.lower() == "excel":
            output_file = output if output.endswith(".xlsx") else f"{output}.xlsx"
            manager.export_excel(output_file)
        elif format.lower() == "csv":
            output_file = output if output.endswith(".csv") else f"{output}.csv"
            manager.export_csv(output_file)
        elif format.lower() == "json":
            output_file = output if output.endswith(".json") else f"{output}.json"
            manager.export_json(output_file)
        elif format.lower() == "html":
            output_file = output if output.endswith(".html") else f"{output}.html"
            visualizer = GanttVisualizer(manager.project)
            visualizer.save_html(output_file)
        else:
            console.print(f"[red]Unknown format: {format}[/red]")
            raise typer.Exit(1)

    console.print(f"[green]Exported to: {output_file}[/green]")


@app.command()
def chart(
    file: str = typer.Argument(..., help="Path to Gantt chart Excel file"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Save to file instead of showing"),
    format: str = typer.Option("html", "--format", "-f", help="Output format: html, png"),
):
    """Generate and display/save Gantt chart visualization."""
    if not load_project(file):
        raise typer.Exit(1)

    visualizer = GanttVisualizer(manager.project)

    if output:
        with console.status("[bold green]Generating chart..."):
            if format.lower() == "html":
                output_file = output if output.endswith(".html") else f"{output}.html"
                visualizer.save_html(output_file)
            elif format.lower() == "png":
                output_file = output if output.endswith(".png") else f"{output}.png"
                visualizer.save_image(output_file, format="png")
            else:
                console.print(f"[red]Unknown format: {format}[/red]")
                raise typer.Exit(1)

        console.print(f"[green]Chart saved to: {output_file}[/green]")
    else:
        console.print("[bold]Opening chart in browser...[/bold]")
        visualizer.show()


@app.command()
def dashboard(
    file: str = typer.Argument(..., help="Path to Gantt chart Excel file"),
    host: str = typer.Option("127.0.0.1", "--host", "-h", help="Host to bind to"),
    port: int = typer.Option(8050, "--port", "-p", help="Port to bind to"),
):
    """Launch interactive web dashboard."""
    if not load_project(file):
        raise typer.Exit(1)

    from gantt_pro.visualization.dashboard import GanttDashboard

    console.print(f"[bold green]Starting dashboard at http://{host}:{port}[/bold green]")
    console.print("[dim]Press Ctrl+C to stop[/dim]")

    dashboard = GanttDashboard(manager)
    dashboard.run(host=host, port=port)


@app.command()
def api(
    file: str = typer.Argument(..., help="Path to Gantt chart Excel file"),
    host: str = typer.Option("127.0.0.1", "--host", "-h", help="Host to bind to"),
    port: int = typer.Option(5000, "--port", "-p", help="Port to bind to"),
):
    """Launch REST API server."""
    if not load_project(file):
        raise typer.Exit(1)

    from gantt_pro.api.routes import run_api

    console.print(f"[bold green]Starting API server at http://{host}:{port}[/bold green]")
    console.print("[dim]Press Ctrl+C to stop[/dim]")

    run_api(manager, host=host, port=port)


@app.command()
def search(
    file: str = typer.Argument(..., help="Path to Gantt chart Excel file"),
    query: str = typer.Argument(..., help="Search query"),
):
    """Search for tasks by name."""
    if not load_project(file):
        raise typer.Exit(1)

    results = manager.search_tasks(query)

    if not results:
        console.print(f"[yellow]No tasks found matching '{query}'[/yellow]")
        raise typer.Exit(0)

    console.print(f"[bold]Found {len(results)} task(s) matching '{query}':[/bold]\n")

    for task in results:
        status_color = {
            TaskStatus.COMPLETED: "green",
            TaskStatus.IN_PROGRESS: "yellow",
            TaskStatus.NOT_STARTED: "dim",
        }.get(task.status, "white")

        console.print(Panel(
            f"[bold]{task.name}[/bold]\n"
            f"Category: {task.category or 'N/A'} | Owner: {task.owner or 'N/A'}\n"
            f"Duration: {format_duration(task.duration)} | Progress: {task.progress:.0f}%\n"
            f"Dates: {format_date(task.start_date)} to {format_date(task.end_date)}",
            title=f"[{status_color}]{task.wbs or 'Task'}[/{status_color}]",
            border_style=status_color,
        ))


@app.command()
def update(
    file: str = typer.Argument(..., help="Path to Gantt chart Excel file"),
    task_id: str = typer.Argument(..., help="Task ID or WBS number"),
    progress_value: Optional[float] = typer.Option(None, "--progress", "-p", help="Update progress (0-100)"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Save to new file"),
):
    """Update a task's properties."""
    if not load_project(file):
        raise typer.Exit(1)

    # Find task by ID or WBS
    task = manager.project.get_task(task_id)
    if not task:
        # Try by WBS
        for t in manager.project.all_tasks:
            if t.wbs == task_id:
                task = t
                break

    if not task:
        console.print(f"[red]Task not found: {task_id}[/red]")
        raise typer.Exit(1)

    updates = {}
    if progress_value is not None:
        updates["progress"] = progress_value

    if updates:
        manager.update_task(task.id, **updates)
        console.print(f"[green]Updated task: {task.name}[/green]")

        # Save if output specified
        if output:
            manager.export_excel(output)
            console.print(f"[green]Saved to: {output}[/green]")
    else:
        console.print("[yellow]No updates specified[/yellow]")


@app.command()
def categories(
    file: str = typer.Argument(..., help="Path to Gantt chart Excel file"),
):
    """List all categories with task counts."""
    if not load_project(file):
        raise typer.Exit(1)

    breakdown = manager.get_category_breakdown()

    table = Table(title="Categories", show_header=True, header_style="bold magenta")
    table.add_column("Category", style="cyan")
    table.add_column("Tasks", justify="right")
    table.add_column("Completed", justify="right", style="green")
    table.add_column("Duration", justify="right")
    table.add_column("Avg Progress", justify="right")

    for cat_name, data in breakdown.items():
        table.add_row(
            cat_name,
            str(data["count"]),
            str(data["completed"]),
            format_duration(data["total_duration"]),
            f"{data['avg_progress']:.1f}%",
        )

    console.print(table)


@app.command()
def version():
    """Show version information."""
    from gantt_pro import __version__
    console.print(f"[bold]Gantt Pro[/bold] version {__version__}")


def main():
    """Main entry point."""
    app()


if __name__ == "__main__":
    main()
