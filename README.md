# Travel Planner Generator

DTS114TC AI Software Engineering coursework project.

This project builds an AI-powered system for meta-software development. It generates SDLC documentation, UML diagrams, a Flask API, a travel planning website, tests, CI workflow configuration, and Docker deployment files.

The selected business problem is a travel planner website. Users enter a destination, trip length, budget, interests, and travel style. The generated Flask API returns a day-by-day itinerary, and the website requests an AI-generated destination image at runtime.

The website uses two AI-generated images. First, the notebook generates a default travel-planner website image and saves it into the generated website assets. This image is visible when the website first loads. Second, after the user submits a destination, the website calls the generated Flask API to create a destination-specific AI image based on the user's input.

## Structure

```text
Task1/
  travel_planner_generator.ipynb
  ai_in_se_cw.yml

Task2/
  app/
    app.py
    index.html
    requirements.txt
    Dockerfile
  docs/
  tests/
  uml/
  deployment.md
```

## Environment

To run the notebook, use Python/Jupyter with:

```text
requests
python-dotenv
flask
flask-cors
pytest
```

The coursework conda environment file is included at:

```text
Task1/ai_in_se_cw.yml
```

An APIFree API key should be provided as `APIFREE_API_KEY` in the submitted `.env` file or as an environment variable. Internet access is required for APIFree generation and PlantUML rendering.

The submitted `.env` file should use this format:

```text
APIFREE_API_KEY=your_key_here
APIFREE_BASE_URL=https://api.apifree.ai/v1
APIFREE_MODEL=gpt-5-mini
APIFREE_IMAGE_MODEL=google/nano-banana-2
```

## Run Task1 Notebook

Open and run:

```text
Task1/travel_planner_generator.ipynb
```

The notebook generates the Task2 artefacts, including documentation, UML diagrams, Flask API code, website code, tests, CI workflow configuration, Docker deployment files, and a default AI-generated website image.

The recommended layout is to run the notebook from `Task1`. If the notebook is run from a standalone folder, it will use the current working directory as the project root and create a `Task2` folder there.

## Run Tests

From the project root:

```powershell
python -m pytest Task2/tests -q
```

## Docker Deployment

Open a terminal from the project root, then move into the generated Flask app folder:

```powershell
cd "Task2/app"
```

Build and run the Docker image:

```powershell
docker build -t travel-planner-generator .
docker run --rm -p 5000:5000 --env-file ../../.env travel-planner-generator
```

The `--env-file ../../.env` path assumes the `.env` file is in the project root, two levels above `Task2/app`.

Then open:

```text
http://localhost:5000
```

## Optional: Run Website Without Docker

From `Task2/app`:

```powershell
python app.py
```

Then open:

```text
http://localhost:5000
```

## CI/CD

The GitHub Actions workflow is stored at:

```text
.github/workflows/ci.yml
```

It installs dependencies and runs the pytest test suite on push and pull request events.

## Coursework Evidence

Suggested screenshots for Task2:

- Commit records: GitHub repository commit history.
- CI/CD workflow: GitHub Actions page showing the `Travel Planner CI` workflow passing.
- Website deployment: browser showing the running website at `http://localhost:5000`.
