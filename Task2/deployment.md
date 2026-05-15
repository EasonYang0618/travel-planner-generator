# Deployment Notes

The generated Travel Planner Generator can be deployed with Docker.

## Build

Run from `Task2/app`:

```powershell
docker build -t travel-planner-generator .
```

## Run

Run with the APIFree key supplied as an environment variable:

```powershell
docker run --rm -p 5000:5000 --env-file ../../.env travel-planner-generator
```

Then open:

```text
http://localhost:5000
```

## Evidence

For the coursework deployment screenshot, capture the running website in the browser at `http://localhost:5000`.
