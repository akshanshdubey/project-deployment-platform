import os
import subprocess

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://admin:password@postgres:5432/deployment_platform"

db = SQLAlchemy(app)

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    repo_url = db.Column(db.String(500))
    status = db.Column(db.String(50))


@app.route("/projects", methods=["POST"])
def create_project():

    data = request.get_json()

    new_project = Project(
        name=data["name"],
        repo_url=data["repo_url"],
        status="pending"
    )

    db.session.add(new_project)
    db.session.commit()

    return jsonify({
        "message": "Project created successfully"
    })

@app.route("/projects", methods=["GET"])
def get_projects():

    projects = Project.query.all()

    output = []

    for project in projects:
        output.append({
            "id": project.id,
            "name": project.name,
            "repo_url": project.repo_url,
            "status": project.status
        })

    return jsonify(output)

@app.route("/deploy", methods=["POST"])
def deploy_project():

    data = request.get_json()

    repo_url = data["repo_url"]

    project_count = Project.query.count()

    folder_name = f"/app/deployments/project_{project_count + 1}"

    subprocess.run([
        "git",
        "clone",
        repo_url,
        folder_name
    ])

    dockerfile_path = os.path.join(folder_name, "Dockerfile")

    if not os.path.exists(dockerfile_path):
        return jsonify({
            "error": "Dockerfile not found"
        }), 400

    return jsonify({
        "message": "Repository cloned successfully",
        "folder": folder_name
    })  

if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(host="0.0.0.0", port=5000)