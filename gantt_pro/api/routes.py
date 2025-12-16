"""
REST API routes for Gantt Pro (Flask-based).
"""

from flask import Flask, jsonify, request, send_file
from datetime import date
from typing import Optional
import tempfile
import os

from gantt_pro.core.manager import GanttManager
from gantt_pro.visualization.charts import GanttVisualizer


def create_api(manager: Optional[GanttManager] = None) -> Flask:
    """Create Flask API application."""

    app = Flask(__name__)
    app.manager = manager or GanttManager()

    @app.route("/api/health", methods=["GET"])
    def health():
        """Health check endpoint."""
        return jsonify({"status": "ok", "version": "1.0.0"})

    @app.route("/api/project", methods=["GET"])
    def get_project():
        """Get project information."""
        if not app.manager.project:
            return jsonify({"error": "No project loaded"}), 404
        return jsonify(app.manager.project.to_dict())

    @app.route("/api/project/summary", methods=["GET"])
    def get_project_summary():
        """Get project summary statistics."""
        if not app.manager.project:
            return jsonify({"error": "No project loaded"}), 404
        return jsonify(app.manager.project.summary())

    @app.route("/api/project/statistics", methods=["GET"])
    def get_statistics():
        """Get detailed project statistics."""
        if not app.manager.project:
            return jsonify({"error": "No project loaded"}), 404
        return jsonify(app.manager.get_statistics())

    @app.route("/api/tasks", methods=["GET"])
    def get_tasks():
        """Get all tasks."""
        if not app.manager.project:
            return jsonify({"error": "No project loaded"}), 404

        tasks = app.manager.project.all_tasks

        # Apply filters
        category = request.args.get("category")
        owner = request.args.get("owner")
        status = request.args.get("status")

        if category:
            tasks = [t for t in tasks if t.category == category]
        if owner:
            tasks = [t for t in tasks if t.owner == owner]
        if status:
            tasks = [t for t in tasks if t.status.value == status]

        return jsonify([t.to_dict() for t in tasks])

    @app.route("/api/tasks/<task_id>", methods=["GET"])
    def get_task(task_id):
        """Get a specific task."""
        if not app.manager.project:
            return jsonify({"error": "No project loaded"}), 404

        task = app.manager.project.get_task(task_id)
        if not task:
            return jsonify({"error": "Task not found"}), 404

        return jsonify(task.to_dict())

    @app.route("/api/tasks", methods=["POST"])
    def create_task():
        """Create a new task."""
        if not app.manager.project:
            return jsonify({"error": "No project loaded"}), 404

        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        try:
            # Parse dates if provided
            if data.get("start_date"):
                data["start_date"] = date.fromisoformat(data["start_date"])
            if data.get("end_date"):
                data["end_date"] = date.fromisoformat(data["end_date"])

            task = app.manager.add_task(**data)
            return jsonify(task.to_dict()), 201

        except Exception as e:
            return jsonify({"error": str(e)}), 400

    @app.route("/api/tasks/<task_id>", methods=["PUT", "PATCH"])
    def update_task(task_id):
        """Update a task."""
        if not app.manager.project:
            return jsonify({"error": "No project loaded"}), 404

        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        try:
            # Parse dates if provided
            if data.get("start_date"):
                data["start_date"] = date.fromisoformat(data["start_date"])
            if data.get("end_date"):
                data["end_date"] = date.fromisoformat(data["end_date"])

            task = app.manager.update_task(task_id, **data)
            if not task:
                return jsonify({"error": "Task not found"}), 404

            return jsonify(task.to_dict())

        except Exception as e:
            return jsonify({"error": str(e)}), 400

    @app.route("/api/tasks/<task_id>", methods=["DELETE"])
    def delete_task(task_id):
        """Delete a task."""
        if not app.manager.project:
            return jsonify({"error": "No project loaded"}), 404

        if app.manager.delete_task(task_id):
            return jsonify({"status": "deleted"})
        return jsonify({"error": "Task not found"}), 404

    @app.route("/api/tasks/<task_id>/progress", methods=["PUT"])
    def update_progress(task_id):
        """Update task progress."""
        if not app.manager.project:
            return jsonify({"error": "No project loaded"}), 404

        data = request.get_json()
        progress = data.get("progress")

        if progress is None:
            return jsonify({"error": "Progress value required"}), 400

        task = app.manager.update_progress(task_id, float(progress))
        if not task:
            return jsonify({"error": "Task not found"}), 404

        return jsonify(task.to_dict())

    @app.route("/api/categories", methods=["GET"])
    def get_categories():
        """Get list of categories."""
        if not app.manager.project:
            return jsonify({"error": "No project loaded"}), 404

        categories = list(set(
            t.category for t in app.manager.project.all_tasks
            if t.category
        ))
        return jsonify(categories)

    @app.route("/api/owners", methods=["GET"])
    def get_owners():
        """Get list of owners."""
        if not app.manager.project:
            return jsonify({"error": "No project loaded"}), 404

        owners = list(set(
            t.owner for t in app.manager.project.all_tasks
            if t.owner
        ))
        return jsonify(owners)

    @app.route("/api/export/excel", methods=["GET"])
    def export_excel():
        """Export project to Excel."""
        if not app.manager.project:
            return jsonify({"error": "No project loaded"}), 404

        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
            output_path = f.name

        app.manager.export_excel(output_path)
        return send_file(
            output_path,
            as_attachment=True,
            download_name=f"{app.manager.project.name or 'gantt'}.xlsx"
        )

    @app.route("/api/export/csv", methods=["GET"])
    def export_csv():
        """Export project to CSV."""
        if not app.manager.project:
            return jsonify({"error": "No project loaded"}), 404

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            output_path = f.name

        app.manager.export_csv(output_path)
        return send_file(
            output_path,
            as_attachment=True,
            download_name=f"{app.manager.project.name or 'gantt'}.csv"
        )

    @app.route("/api/export/json", methods=["GET"])
    def export_json():
        """Export project to JSON."""
        if not app.manager.project:
            return jsonify({"error": "No project loaded"}), 404

        return jsonify(app.manager.project.to_dict())

    @app.route("/api/chart/html", methods=["GET"])
    def get_chart_html():
        """Get Gantt chart as HTML."""
        if not app.manager.project:
            return jsonify({"error": "No project loaded"}), 404

        visualizer = GanttVisualizer(app.manager.project)
        fig = visualizer.create_gantt_chart()
        return fig.to_html()

    @app.route("/api/timeline", methods=["GET"])
    def get_timeline():
        """Get timeline data for visualization."""
        if not app.manager.project:
            return jsonify({"error": "No project loaded"}), 404

        return jsonify(app.manager.get_timeline_data())

    return app


def run_api(manager: GanttManager, host: str = "127.0.0.1",
            port: int = 5000, debug: bool = True) -> None:
    """Run the API server."""
    app = create_api(manager)
    app.run(host=host, port=port, debug=debug)
