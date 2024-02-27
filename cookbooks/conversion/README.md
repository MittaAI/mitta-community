
# AI Powered Media Conversion Pipeline

This pipeline is designed to convert and process media files using an `aiffmpeg` processor, transforming them via AI-generated conversion code. It enables users to automate the transformation of various media formats and integrate advanced AI capabilities into their media processing workflows.

It can be used with file generation pipelines to resize/reformat images or audio files.

## Video Guide

Watch the video guide before beginning installation.

[![conversion](https://img.youtube.com/vi/zAdhqL1yr5Y/0.jpg)](https://www.youtube.com/watch?v=zAdhqL1yr5Y)

## Install

Add the pipelines in this directory to [MittaAI](https://mitta.ai) from the `pipelines` page. The first pipeline defaults to resizing PNGs and calling another pipeline back to log the output. The first pipeline expects the second pipeline to be called `ffmpegupload`, but could be changed to do a callback to a custom endpoint.

## Use

You can test the pipeline using the `upload` button on the pipeline detail page, or you can do a request with `curl`:

Resize an image:
```
convert to a 256 x 256 png
```

Resize an audio file and convert it:
```
convert to an mp3 and make it start at 1 minute and last for 30 seconds
```

### Example

The POST requires an image file.
```
curl -X POST "http://localhost:8080/pipeline/zeXeO6d0IiQdF/task?token=<token>" \
-H "Content-Type: multipart/form-data" \
-F "file=@chest.png;type=image/png"
```

### Sample Output

<img src="https://raw.githubusercontent.com/MittaAI/mitta-community/main/cookbooks/conversion/images/7GjzjSoj8V7OB.png">

If you have issues configuring the pipeline, pop into [Slack](https://join.slack.com/t/mittaai/shared_invite/zt-2azbcv29i-CL74lmOksgvN54jhvmVWeA).

## Docker Instance Integration

The Docker instance is seamlessly integrated with the conversion pipeline, allowing for the use of MittaAI directly by uploading files to it. A [demo](https://convert.mitta.ai) of this is available. This integration facilitates a streamlined workflow, enhancing the utility and accessibility of MittaAI for various conversion tasks.

### Launching the Docker Container

To launch the Docker container, follow these steps:

- **Edit Configuration**: Modify the `sample_config.json` file and save it as `config.json` to customize your setup based on your specific requirements.

- **Start the Container**: Use the `dev.ps1` script to initiate the Docker container. This script is designed for Docker Desktop on Windows, streamlining the startup process and ensuring the container runs with the correct configuration.

This setup provides a robust framework for utilizing the conversion capabilities within MittaAI, making it easier for users to integrate conversion tasks into their workflows.

## Google Cloud Run Integration

For an enhanced automation experience, our Docker instance supports integration with Google Cloud Run. This allows for continuous deployment by monitoring updates to a specified GitHub repository.

### Setting Up Integration

To connect your Docker instance with Google Cloud Run:

1. **Google Cloud Run Setup**: In your Google Cloud Console, navigate to the Cloud Run section and select the option to create a new service.

2. **Repository Monitoring**: Configure the service to monitor your GitHub repository for changes. This setup will trigger automatic deployments whenever updates are detected in the specified branches or directories.

3. **Deployment Configuration**: Ensure your Docker container is configured to meet the requirements of Google Cloud Run, including environment variables and resource allocations.

### Need Help?

Integrating Google Cloud Run with your workflow can streamline deployments and enhance your CI/CD pipeline. If you encounter any issues or have questions about setting up this integration, don't hesitate to reach out to us on Slack for assistance and more information.

[Join our Slack community](https://join.slack.com/t/mittaai/shared_invite/zt-2azbcv29i-CL74lmOksgvN54jhvmVWeA) to connect with our team and fellow users who can help guide you through the process and share their insights.
