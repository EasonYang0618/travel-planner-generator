# Dynamic destination image generation

The generated Flask application uses two AI image mechanisms. First, the notebook generates a default website hero image and saves it as `Task2/app/static/images/travel_planner_hero.png`, so the deployed website can show an automatically generated image before any user input. Second, when a user submits a destination, interests, and travel style, the frontend calls `/api/destination-image`. The backend builds a fresh image prompt from those user inputs, sends it to the APIFree image API, saves the returned image in `Task2/app/generated_images/`, and returns the local image URL to the page.

This means the website can show a default generated image immediately and can later generate a new destination-specific image for Kyoto, Paris, Shanghai, New York, or another destination entered by the user.
