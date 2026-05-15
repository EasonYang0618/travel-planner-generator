# Travel Planner Generator

DTS114TC AI Software Engineering coursework project.

This project builds an AI-powered system for meta-software development. It generates SDLC documentation, UML diagrams, a Flask API, a travel planning website, tests, CI workflow configuration, and Docker deployment files.

The selected business problem is a travel planner website. Users enter a destination, trip length, budget, interests, and travel style. The generated Flask API returns a day-by-day itinerary, and the website requests an AI-generated destination image at runtime.

## Structure

```text
Task1/
  travel_planner_generator.ipynb

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

An APIFree API key should be provided as `APIFREE_API_KEY` in a `.env` file or as an environment variable. Internet access is required for APIFree generation and PlantUML rendering.

Example `.env` values:

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

The notebook generates the Task2 artefacts, including documentation, UML diagrams, Flask API code, website code, tests, CI workflow configuration, and Docker deployment files.

## Run Tests

From the project root:

```powershell
python -m pytest Task2/tests -q
```

## Docker Deployment

From `Task2/app`:

```powershell
docker build -t travel-planner-generator .
docker run --rm -p 5000:5000 --env-file ../../.env travel-planner-generator
```

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
