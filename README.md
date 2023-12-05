# Welcome to MittaAI
This is the community repository for MittaAI and SlothAI users. All code or examples here are covered by the [MIT software license](https://github.com/MittaAI/mitta-community/blob/main/LICENSE).

The SlothAI framework, which runs MittaAI, is located [here](https://github.com/kordless/SlothAI).

There is a [Discord server](https://discord.gg/SxwcVGQ8j9) available for help with building or running pipelines.

## Getting Started Video
Before you begin, we recommend watching the Getting Started video guide. This guide will help you become familiar with important concepts such as callbacks, storage, and how to use pipelines effectively.

[![Getting Started](https://img.youtube.com/vi/ntLqz38hC60/0.jpg)](https://www.youtube.com/watch?v=ntLqz38hC60)

## Pipeline Cookbooks
In the [cookbooks directory](./cookbooks), you'll find a collection of example pipelines that are available for use on MittaAI's website. These pipelines can help you get started quickly. 

## Instructions for Use
### Creating a MittaAI Account
To use these pipelines, you'll need to create a [MittaAI account](https://mitta.ai) if you don't already have one. MittaAI provides a user-friendly platform for running and managing AI pipelines.

### Installing the SlothAI Framework (Optional)
If you prefer to use the pipelines locally on Google Cloud, you can install the [SlothAI framework](https://github.com/kordless/SlothAI). This framework allows you to run AI pipelines in your own environment.

### Storage Requirements
Please note that some pipelines may require storage. For this purpose, you will need a [FeatureBase Cloud](https://cloud.featurebase.com) account. FeatureBase Cloud provides a cloud-based storage solution for AI pipeline data.

SlothAI will eventually support other database storage layers, providing more flexibility.

### Importing a Pipeline
To import a pipeline, follow these steps:

1. [Download](https://github.com/MittaAI/mitta-community/archive/refs/heads/main.zip) this repository locally.
1. Unzip it and place the directory somewhere reasonable on your drive.
1. Navigate to the [pipelines](https://mitta.ai/pipelines) tab in MittaAI.
1. Click on the import option.
1. Choose the pipeline you would like to import from the cookbooks directory.
1. Keep in mind that if there are multiple pipelines for a cookbook, you will need to import them separately.
1. Fill in any additional tokens or parameters as prompted.

## Contributing
If you have a pipeline you'd like to contribute, please do a PR for it.

The PR will be more likely to be added quickly if the following is true:
1. A new directory under `cookbooks` with a unique and short name.
1. The pipeline export file should remain JSON formatted.
1. Pipeline, node and template names should be unique and short.
1. Prompts, variables, comments and other named objects should be reasonable.
1. The pipeline runs successfully.
1. A `README.md` file that clearly explains how to use the pipeline.
1. Any supporting materials, organized by reasonable directory structure.
