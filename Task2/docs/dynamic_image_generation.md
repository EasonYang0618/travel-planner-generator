# Dynamic destination image generation

The generated Flask application creates destination images at runtime. When a user submits a destination, interests, and travel style, the frontend calls `/api/destination-image`. The backend builds a fresh image prompt from those user inputs, sends it to the APIFree image API, saves the returned image in `Task2/app/generated_images/`, and returns the local image URL to the page.

This means the website is not fixed to the demonstration destination. The same app can generate a new image for Kyoto, Paris, Shanghai, New York, or another destination entered by the user.
