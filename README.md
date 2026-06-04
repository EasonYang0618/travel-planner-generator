# Travel Planner Generator

DTS114TC AI Software Engineering coursework project.

> **Note on AI-generated artefacts:** Because this project uses AI to generate code and documentation, there is a small chance that one regenerated output may differ and cause a test issue. The submitted version has been tested, but if this happens after re-running the notebook, please run the notebook again to regenerate the artefacts.

This project builds an AI-powered system for meta-software development. It generates SDLC documentation, UML diagrams, a Flask API, a travel planning website, tests, CI workflow configuration, and Docker deployment files.

The selected business problem is a travel planner website. Users enter a destination, trip length, budget, interests, and travel style. The generated Flask API returns a day-by-day itinerary, and the website requests an AI-generated destination image at runtime.

The website uses two AI-generated images. First, the notebook generates a default travel-planner website image and saves it into the generated website assets. This image is visible when the website first loads. Second, after the user submits a destination, the website calls the generated Flask API to create a destination-specific AI image based on the user's input.

The generated website has also been deployed on Render:

```text
https://travel-planner-generator.onrender.com
```

The destination image is generated only after the user enters a destination and submits the form. Because the Render deployment is created under my Render account, the Render environment variables must be configured by me before testing. Therefore, I configured my own APIFree API key for the deployed site and added 10 USD credit so that the marker can test the runtime image generation feature.

The notebook also uses a lightweight frontend image contract agent. This agent checks the AI-generated frontend for the default image, destination image area, and `/api/destination-image` call. If one part is missing, it adds only that frontend integration and records its actions in `Task1/artifacts/docs/frontend_image_contract_agent_report.md`.

## Structure

```text
Task1/
  travel_planner_generator.ipynb
  ai_in_se_cw.yml
  artifacts/
    app/
      app.py
      index.html
      requirements.txt
      Dockerfile
    docs/
      frontend_image_contract_agent_report.md
    tests/
    uml/
    deployment.md

Task2/
  screenshots/
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

An APIFree API key should be provided as `APIFREE_API_KEY` in the submitted `.env` file or as an environment variable. Internet access is required for APIFree generation and PlantUML rendering. For the Render deployment, I used my own APIFree key and added 10 USD credit because the cloud environment variables are configured from my Render account. If the key later runs out of balance, please replace it with another valid APIFree key when running locally.

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

The notebook generates the coursework artefacts under `Task1/artifacts`, including documentation, UML diagrams, Flask API code, website code, tests, Docker deployment files, and a default AI-generated website image.

During frontend generation, the notebook runs the lightweight frontend image contract agent. It does not replace the generated app; it only checks and stabilises the image integration.

The recommended layout is to run the notebook from `Task1`. The generated output is written to `Task1/artifacts`.

## Run Tests

From the project root:

```powershell
python -m pytest Task1/artifacts/tests -q
```

## Docker Deployment

Open a terminal from the project root, then move into the generated Flask app folder:

```powershell
cd "Task1/artifacts/app"
```

Build and run the Docker image:

```powershell
docker build -t travel-planner-generator .
docker run --rm -p 5000:5000 --env-file ../../../.env travel-planner-generator
```

The `--env-file ../../../.env` path assumes the `.env` file is in the project root, three levels above `Task1/artifacts/app`.

Then open:

```text
http://localhost:5000
```

## Render Cloud Deployment

The submitted website is deployed on Render at:

```text
https://travel-planner-generator.onrender.com
```

Render runs the generated Flask app from `Task1/artifacts/app`. Since this deployment is managed from my Render account, I pre-configured my own APIFree key in the Render environment variables and added 10 USD credit. This is to ensure that the deployed website can call APIFree when the marker submits a destination and tests the destination-specific AI image generation feature.

## Optional: Run Website Without Docker

From `Task1/artifacts/app`:

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
- Website deployment: browser showing the Render deployment at `https://travel-planner-generator.onrender.com`.
