const API_URL = "http://13.235.99.38:5001"

async function loadProjects() {

    const response = await fetch(`${API_URL}/projects`)

    const projects = await response.json()

    const container = document.getElementById("projectsContainer")

    container.innerHTML = ""

    projects.forEach(project => {

        container.innerHTML += `
            <div class="project-card">
                <h3>${project.name}</h3>

                <p>Status: ${project.status}</p>

                <p>Port: ${project.deployed_port || "Not deployed"}</p>

                ${
                    project.deployed_port
                    ? `<a href="http://13.235.99.38:${project.deployed_port}" target="_blank">
                        Open App
                      </a>`
                    : ""
                }
            </div>
        `
    })
}

async function deployProject() {

    const repoUrl = document.getElementById("repoUrl").value

    if (!repoUrl) {
        alert("Enter repository URL")
        return
    }

    const response = await fetch(`${API_URL}/deploy`, {
        method: "POST",

        headers: {
            "Content-Type": "application/json"
        },

        body: JSON.stringify({
            repo_url: repoUrl
        })
    })

    const data = await response.json()

    alert(data.message || data.error)

    loadProjects()
}

loadProjects()