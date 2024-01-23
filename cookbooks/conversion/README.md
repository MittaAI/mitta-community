# AI Powered Media Conversion Pipeline
This pipeline is designed to convert and process media files using an `aiffmpeg` processor, transforming them via AI-generated conversion code. It enables users to automate the transformation of various media formats and integrate advanced AI capabilities into their media processing workflows.

It can be used with file generation pipelines to resize/reformat images or audio files.

## Video Guide
Watch the video guide before beginning installation.

[![conversion](https://img.youtube.com/vi/zAdhqL1yr5Y/0.jpg)](https://www.youtube.com/watch?v=zAdhqL1yr5Y)

## Install
Add the pipelines in this directory to [MittaAI](https://mitta.ai) from the `pipelines` page. The first pipeline defaults to resizing PNGs and calling another pipeline back to log the output. The first pipeline expect the second pipeline to be called `ffmpegupload`, but could be changed to do a callback to a custom endpoint.

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