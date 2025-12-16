#!/usr/bin/env python3
"""
Gantt Pro Demo Script
=====================

This script demonstrates the main features of Gantt Pro.
"""

import sys
sys.path.insert(0, '.')

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import print as rprint

from gantt_pro.core.manager import GanttManager
from gantt_pro.core.models import TaskStatus
from gantt_pro.visualization.charts import GanttVisualizer
from gantt_pro.utils.helpers import format_date, format_duration, progress_bar

console = Console()


def main():
    console.print(Panel.fit(
        "[bold blue]Gantt Pro Demo[/bold blue]\n"
        "Professional Gantt Chart Analysis and Management",
        border_style="blue"
    ))

    # Load the Gantt chart
    console.print("\n[bold]1. Loading Gantt Chart...[/bold]")
    manager = GanttManager("Gantt chart.xlsx")

    # Project info
    console.print("\n[bold]2. Project Information:[/bold]")
    project = manager.project
    console.print(f"   Project: [cyan]{project.name}[/cyan]")
    console.print(f"   Manager: [green]{project.manager}[/green]")
    console.print(f"   Company: [blue]{project.company}[/blue]")

    # Statistics
    console.print("\n[bold]3. Project Statistics:[/bold]")
    stats = manager.get_statistics()

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Metric")
    table.add_column("Value", justify="right")

    table.add_row("Total Tasks", str(stats["total_tasks"]))
    table.add_row("Completed", f"[green]{stats['completed']}[/green]")
    table.add_row("In Progress", f"[yellow]{stats['in_progress']}[/yellow]")
    table.add_row("Not Started", str(stats["not_started"]))
    table.add_row("Overdue", f"[red]{stats['overdue']}[/red]")
    table.add_row("Overall Progress", f"{stats['overall_progress']:.1f}%")

    console.print(table)

    # Progress bar
    console.print(f"\n   Overall: {progress_bar(stats['overall_progress'], width=40)}")

    # Category breakdown
    console.print("\n[bold]4. Category Breakdown:[/bold]")
    for cat_name, cat_data in stats["categories"].items():
        avg_progress = cat_data["avg_progress"]
        console.print(f"   {cat_name:25} {progress_bar(avg_progress, width=30)}")

    # Task list sample
    console.print("\n[bold]5. Sample Tasks (first 10):[/bold]")

    task_table = Table(show_header=True, header_style="bold cyan")
    task_table.add_column("WBS", width=8)
    task_table.add_column("Task", max_width=35)
    task_table.add_column("Category", width=12)
    task_table.add_column("Owner", width=10)
    task_table.add_column("Progress", width=10)

    for task in project.all_tasks[:10]:
        status_style = {
            TaskStatus.COMPLETED: "green",
            TaskStatus.IN_PROGRESS: "yellow",
            TaskStatus.NOT_STARTED: "dim",
        }.get(task.status, "white")

        task_table.add_row(
            task.wbs or "-",
            task.name[:35],
            task.category or "-",
            task.owner or "-",
            f"[{status_style}]{task.progress:.0f}%[/{status_style}]",
        )

    console.print(task_table)

    # Export options
    console.print("\n[bold]6. Available Exports:[/bold]")
    console.print("   - manager.export_excel('output.xlsx')")
    console.print("   - manager.export_csv('output.csv')")
    console.print("   - manager.export_json('output.json')")

    # Visualization
    console.print("\n[bold]7. Visualization Options:[/bold]")
    console.print("   - GanttVisualizer(project).show()       # Interactive browser view")
    console.print("   - GanttVisualizer(project).save_html()  # Save as HTML")
    console.print("   - run_dashboard('file.xlsx')            # Web dashboard")

    # Interactive options
    console.print("\n[bold]8. Would you like to:[/bold]")
    console.print("   [1] View interactive Gantt chart in browser")
    console.print("   [2] Export to Excel")
    console.print("   [3] Export to HTML")
    console.print("   [4] Start web dashboard")
    console.print("   [5] Exit")

    choice = input("\nEnter choice (1-5): ").strip()

    if choice == "1":
        console.print("\n[bold green]Opening Gantt chart in browser...[/bold green]")
        visualizer = GanttVisualizer(project)
        visualizer.show()

    elif choice == "2":
        output_file = "gantt_export.xlsx"
        manager.export_excel(output_file)
        console.print(f"\n[bold green]Exported to {output_file}[/bold green]")

    elif choice == "3":
        output_file = "gantt_chart.html"
        visualizer = GanttVisualizer(project)
        visualizer.save_html(output_file)
        console.print(f"\n[bold green]Exported to {output_file}[/bold green]")

    elif choice == "4":
        console.print("\n[bold green]Starting web dashboard at http://localhost:8050[/bold green]")
        console.print("[dim]Press Ctrl+C to stop[/dim]")
        from gantt_pro.visualization.dashboard import GanttDashboard
        dashboard = GanttDashboard(manager)
        dashboard.run()

    else:
        console.print("\n[bold]Goodbye![/bold]")


if __name__ == "__main__":
    main()
