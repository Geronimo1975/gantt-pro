"""
Interactive Web Dashboard for Gantt Chart Management using Dash.
"""

from dash import Dash, html, dcc, callback, Output, Input, State, dash_table
import dash_bootstrap_components as dbc
from datetime import date
from typing import Optional
import pandas as pd

from gantt_pro.core.models import Project, TaskStatus
from gantt_pro.core.manager import GanttManager
from gantt_pro.visualization.charts import GanttVisualizer


class GanttDashboard:
    """Interactive web dashboard for Gantt chart management."""

    def __init__(self, manager: Optional[GanttManager] = None):
        """Initialize dashboard with optional manager."""
        self.manager = manager or GanttManager()
        self.visualizer = GanttVisualizer()
        self.app: Optional[Dash] = None

    def load_file(self, file_path: str) -> None:
        """Load a Gantt chart file."""
        self.manager.load(file_path)
        if self.manager.project:
            self.visualizer.set_project(self.manager.project)

    def _create_layout(self) -> html.Div:
        """Create the dashboard layout."""
        return dbc.Container([
            # Header
            dbc.Row([
                dbc.Col([
                    html.H1("Gantt Pro Dashboard", className="text-primary mb-0"),
                    html.P(
                        f"Project: {self.manager.project.name if self.manager.project else 'No project loaded'}",
                        className="text-muted"
                    ),
                ], width=8),
                dbc.Col([
                    dbc.Button("Export Excel", id="btn-export-excel", color="success", className="me-2"),
                    dbc.Button("Export HTML", id="btn-export-html", color="info", className="me-2"),
                    dbc.Button("Refresh", id="btn-refresh", color="secondary"),
                ], width=4, className="text-end"),
            ], className="my-4"),

            # Statistics Cards
            dbc.Row([
                dbc.Col(self._create_stat_card("Total Tasks", "stat-total", "primary"), width=3),
                dbc.Col(self._create_stat_card("Completed", "stat-completed", "success"), width=3),
                dbc.Col(self._create_stat_card("In Progress", "stat-progress", "warning"), width=3),
                dbc.Col(self._create_stat_card("Overdue", "stat-overdue", "danger"), width=3),
            ], className="mb-4"),

            # Progress Bar
            dbc.Row([
                dbc.Col([
                    html.Label("Overall Progress", className="fw-bold"),
                    dbc.Progress(id="progress-bar", value=0, striped=True, animated=True, className="mb-4"),
                ]),
            ]),

            # Main Gantt Chart
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            html.H5("Gantt Chart", className="mb-0 d-inline"),
                            dbc.ButtonGroup([
                                dbc.Button("Category", id="btn-color-cat", size="sm", outline=True, color="primary"),
                                dbc.Button("Owner", id="btn-color-owner", size="sm", outline=True, color="primary"),
                                dbc.Button("Status", id="btn-color-status", size="sm", outline=True, color="primary"),
                            ], className="float-end"),
                        ]),
                        dbc.CardBody([
                            dcc.Graph(id="gantt-chart", style={"height": "600px"}),
                        ]),
                    ]),
                ]),
            ], className="mb-4"),

            # Analytics Row
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Progress by Category"),
                        dbc.CardBody([
                            dcc.Graph(id="chart-progress-cat", style={"height": "350px"}),
                        ]),
                    ]),
                ], width=6),
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Task Status Distribution"),
                        dbc.CardBody([
                            dcc.Graph(id="chart-status", style={"height": "350px"}),
                        ]),
                    ]),
                ], width=6),
            ], className="mb-4"),

            # Owner Workload Row
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Owner Workload"),
                        dbc.CardBody([
                            dcc.Graph(id="chart-workload", style={"height": "350px"}),
                        ]),
                    ]),
                ], width=6),
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Timeline Heatmap"),
                        dbc.CardBody([
                            dcc.Graph(id="chart-heatmap", style={"height": "350px"}),
                        ]),
                    ]),
                ], width=6),
            ], className="mb-4"),

            # Data Table
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            html.H5("Task List", className="mb-0 d-inline"),
                            dbc.Input(
                                id="task-search",
                                placeholder="Search tasks...",
                                type="text",
                                className="float-end",
                                style={"width": "300px"},
                            ),
                        ]),
                        dbc.CardBody([
                            dash_table.DataTable(
                                id="task-table",
                                columns=[
                                    {"name": "WBS", "id": "WBS"},
                                    {"name": "Task", "id": "Task Name"},
                                    {"name": "Category", "id": "Category"},
                                    {"name": "Owner", "id": "Owner"},
                                    {"name": "Start", "id": "Start Date"},
                                    {"name": "End", "id": "End Date"},
                                    {"name": "Progress", "id": "Progress (%)", "editable": True},
                                    {"name": "Status", "id": "Status"},
                                ],
                                data=[],
                                editable=True,
                                filter_action="native",
                                sort_action="native",
                                sort_mode="multi",
                                row_selectable="multi",
                                page_action="native",
                                page_size=15,
                                style_table={"overflowX": "auto"},
                                style_cell={
                                    "textAlign": "left",
                                    "padding": "10px",
                                    "fontSize": "14px",
                                },
                                style_header={
                                    "backgroundColor": "#f8f9fa",
                                    "fontWeight": "bold",
                                },
                                style_data_conditional=[
                                    {
                                        "if": {"filter_query": "{Status} = 'completed'"},
                                        "backgroundColor": "#d4edda",
                                    },
                                    {
                                        "if": {"filter_query": "{Status} = 'in_progress'"},
                                        "backgroundColor": "#fff3cd",
                                    },
                                    {
                                        "if": {"column_id": "Progress (%)"},
                                        "width": "100px",
                                    },
                                ],
                            ),
                        ]),
                    ]),
                ]),
            ], className="mb-4"),

            # Hidden stores
            dcc.Store(id="store-color-by", data="Category"),
            dcc.Store(id="store-data-version", data=0),
            html.Div(id="download-area"),

        ], fluid=True)

    def _create_stat_card(self, title: str, card_id: str, color: str) -> dbc.Card:
        """Create a statistics card."""
        return dbc.Card([
            dbc.CardBody([
                html.H6(title, className="text-muted mb-2"),
                html.H3(id=card_id, className=f"text-{color} mb-0"),
            ]),
        ], className="shadow-sm")

    def _setup_callbacks(self) -> None:
        """Setup Dash callbacks."""

        @self.app.callback(
            [
                Output("stat-total", "children"),
                Output("stat-completed", "children"),
                Output("stat-progress", "children"),
                Output("stat-overdue", "children"),
                Output("progress-bar", "value"),
                Output("progress-bar", "label"),
            ],
            Input("store-data-version", "data"),
        )
        def update_stats(_):
            if not self.manager.project:
                return "0", "0", "0", "0", 0, "0%"

            stats = self.manager.get_statistics()
            progress = stats.get("overall_progress", 0)

            return (
                str(stats.get("total_tasks", 0)),
                str(stats.get("completed", 0)),
                str(stats.get("in_progress", 0)),
                str(stats.get("overdue", 0)),
                progress,
                f"{progress:.1f}%",
            )

        @self.app.callback(
            Output("gantt-chart", "figure"),
            [Input("store-color-by", "data"), Input("store-data-version", "data")],
        )
        def update_gantt(color_by, _):
            if not self.manager.project:
                return {}
            self.visualizer.set_project(self.manager.project)
            return self.visualizer.create_gantt_chart(color_by=color_by)

        @self.app.callback(
            Output("chart-progress-cat", "figure"),
            Input("store-data-version", "data"),
        )
        def update_progress_chart(_):
            if not self.manager.project:
                return {}
            self.visualizer.set_project(self.manager.project)
            return self.visualizer.create_progress_chart("category")

        @self.app.callback(
            Output("chart-status", "figure"),
            Input("store-data-version", "data"),
        )
        def update_status_chart(_):
            if not self.manager.project:
                return {}
            self.visualizer.set_project(self.manager.project)
            return self.visualizer.create_status_pie()

        @self.app.callback(
            Output("chart-workload", "figure"),
            Input("store-data-version", "data"),
        )
        def update_workload_chart(_):
            if not self.manager.project:
                return {}
            self.visualizer.set_project(self.manager.project)
            return self.visualizer.create_owner_workload()

        @self.app.callback(
            Output("chart-heatmap", "figure"),
            Input("store-data-version", "data"),
        )
        def update_heatmap(_):
            if not self.manager.project:
                return {}
            self.visualizer.set_project(self.manager.project)
            return self.visualizer.create_timeline_heatmap()

        @self.app.callback(
            Output("task-table", "data"),
            [Input("store-data-version", "data"), Input("task-search", "value")],
        )
        def update_table(_, search):
            if not self.manager.project:
                return []

            df = self.manager.to_dataframe()

            # Convert dates to strings for display
            for col in ["Start Date", "End Date"]:
                if col in df.columns:
                    df[col] = df[col].astype(str)

            if search:
                mask = df["Task Name"].str.contains(search, case=False, na=False)
                df = df[mask]

            return df.to_dict("records")

        @self.app.callback(
            Output("store-color-by", "data"),
            [
                Input("btn-color-cat", "n_clicks"),
                Input("btn-color-owner", "n_clicks"),
                Input("btn-color-status", "n_clicks"),
            ],
            State("store-color-by", "data"),
        )
        def change_color_by(cat_clicks, owner_clicks, status_clicks, current):
            from dash import ctx
            if not ctx.triggered_id:
                return current

            if ctx.triggered_id == "btn-color-cat":
                return "Category"
            elif ctx.triggered_id == "btn-color-owner":
                return "Owner"
            elif ctx.triggered_id == "btn-color-status":
                return "Status"
            return current

        @self.app.callback(
            Output("store-data-version", "data"),
            Input("btn-refresh", "n_clicks"),
            State("store-data-version", "data"),
        )
        def refresh_data(n_clicks, current):
            return (current or 0) + 1

    def create_app(self) -> Dash:
        """Create and configure the Dash application."""
        self.app = Dash(
            __name__,
            external_stylesheets=[dbc.themes.BOOTSTRAP],
            title="Gantt Pro Dashboard",
        )

        self.app.layout = self._create_layout()
        self._setup_callbacks()

        return self.app

    def run(self, host: str = "127.0.0.1", port: int = 8050,
            debug: bool = True) -> None:
        """Run the dashboard server."""
        if not self.app:
            self.create_app()
        self.app.run_server(host=host, port=port, debug=debug)


def run_dashboard(file_path: str, host: str = "127.0.0.1",
                  port: int = 8050, debug: bool = True) -> None:
    """Convenience function to run dashboard with a file."""
    dashboard = GanttDashboard()
    dashboard.load_file(file_path)
    dashboard.run(host=host, port=port, debug=debug)
