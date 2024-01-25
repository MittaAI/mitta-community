# Mitta-FFmpeg Service Installation Guide

This guide provides detailed instructions for deploying the `mitta-ffmpeg` service on Google Cloud Run and running it locally using Docker. The service uses FFMPEG for media processing and requires an `FFMPEG_TOKEN` for secure operation.

The service expect a full `ffmpeg-command` which can come from you or an LLM. This is the code that is used on MittaAI's website to provide `ffmpeg` support for the `aiffmpeg` processor.

You can try it out here: [https://ai.mitta.ai/convert](https://ai.mitta.ai/convert)

## Prerequisites

- Google Cloud account and project
- Google Cloud SDK
- Docker for local testing
- Access to [MittaAI/mitta-community](https://github.com/MittaAI/mitta-community) repository

## Google Cloud Run Deployment

### Clone the Repository

```bash
git clone https://github.com/MittaAI/mitta-community.git
cd mitta-community/services/ffmpeg
```

### Google Cloud Setup

Authenticate and set your project:

```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

### Build and Push the Docker Image

In the `/services/ffmpeg/docker` directory:

```bash
docker build -t gcr.io/YOUR_PROJECT_ID/mitta-ffmpeg .
docker push gcr.io/YOUR_PROJECT_ID/mitta-ffmpeg
```

### Deploy to Cloud Run

```bash
gcloud run deploy mitta-ffmpeg-service --image gcr.io/YOUR_PROJECT_ID/mitta-ffmpeg --platform managed
```

## Adding `FFMPEG_TOKEN` Secret

### Create the Secret in Google Cloud

```bash
echo -n "your-secret-token" | gcloud secrets create FFMPEG_TOKEN --data-file=-
gcloud secrets add-iam-policy-binding FFMPEG_TOKEN --member=serviceAccount:service-YOUR_PROJECT_NUMBER@gcp-sa-run.iam.gserviceaccount.com --role=roles/secretmanager.secretAccessor
```

### Deploy with the Secret

```bash
gcloud run deploy mitta-ffmpeg-service --image gcr.io/YOUR_PROJECT_ID/mitta-ffmpeg --platform managed --update-secrets=FFMPEG_TOKEN=FFMPEG_TOKEN:latest
```

## Local Docker Setup

### Build the Docker Image

```bash
docker build -t mitta-ffmpeg .
```

### Run with `FFMPEG_TOKEN`

```bash
docker run -p 5000:5000 -e FFMPEG_TOKEN="your-secret-token" mitta-ffmpeg
```

## Verifying the Token

Ensure your application authenticates using `FFMPEG_TOKEN`:

```python
import os

ffmpeg_token = os.environ.get('FFMPEG_TOKEN')

# In your request handling
if request.headers.get('Authorization') == ffmpeg_token:
    # Authorized
else:
    # Unauthorized
```

## Support

For issues, reach out on Slack or open an issue in the GitHub repository.
