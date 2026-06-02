import os
import time
import subprocess

from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static"
)

CORS(app)

app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://admin:password@postgres:5432/deployment_platform"

db = SQLAlchemy(app)


class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    repo_url = db.Column(db.String(500))
    status = db.Column(db.String(50))
    deployed_port = db.Column(db.Integer)


@app.route("/")
def home():
    return render_template("index.html")


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
            "status": project.status,
            "deployed_port": project.deployed_port
        })

    return jsonify(output)


@app.route("/deploy", methods=["POST"])
def deploy_project():

    data = request.get_json()

    repo_url = data["repo_url"]

    deployment_base_path = "/app/deployments"

    os.makedirs(deployment_base_path, exist_ok=True)

    existing_projects = os.listdir(deployment_base_path)

    project_number = len(existing_projects) + 1

    folder_name = f"project_{project_number}"

    full_folder_path = os.path.join(deployment_base_path, folder_name)

    clone_result = subprocess.run([
        "git",
        "clone",
        repo_url,
        full_folder_path
    ], capture_output=True, text=True)

    if clone_result.returncode != 0:
        return jsonify({
            "error": clone_result.stderr
        }), 400

    possible_paths = [
        os.path.join(full_folder_path, "Dockerfile"),
        os.path.join(full_folder_path, "backend", "Dockerfile"),
        os.path.join(full_folder_path, "app", "Dockerfile"),
        os.path.join(full_folder_path, "server", "Dockerfile")
    ]

    dockerfile_path = None

    for path in possible_paths:
        if os.path.exists(path):
            dockerfile_path = path
            break

    if dockerfile_path is None:
        return jsonify({
            "error": "Dockerfile not found"
        }), 400

    docker_context = os.path.dirname(dockerfile_path)

    image_name = f"deployment-image-{project_number}"

    container_name = f"deployment-container-{project_number}"

    deployed_port = 6000 + project_number

    build_result = subprocess.run([
        "docker",
        "build",
        "-t",
        image_name,
        docker_context
    ], capture_output=True, text=True)

    if build_result.returncode != 0:
        return jsonify({
            "error": "Docker build failed",
            "details": build_result.stderr
        }), 400

    run_result = subprocess.run([
        "docker",
        "run",
        "-d",
        "-p",
        f"{deployed_port}:5000",
        "--name",
        container_name,
        image_name
    ], capture_output=True, text=True)

    if run_result.returncode != 0:
        return jsonify({
            "error": "Docker container failed to start",
            "details": run_result.stderr
        }), 400

    new_project = Project(
        name=folder_name,
        repo_url=repo_url,
        status="deployed",
        deployed_port=deployed_port
    )

    db.session.add(new_project)
    db.session.commit()

    return jsonify({
        "message": "Project deployed successfully",
        "container_name": container_name,
        "image_name": image_name,
        "port": deployed_port,
        "url": f"http://13.235.99.38:{deployed_port}"
    })


if __name__ == "__main__":

    while True:
        try:
            with app.app_context():
                db.create_all()

            print("Database connected")
            break

        except Exception as e:
            print("Database not ready yet...")
            print(e)
            time.sleep(5)

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
