# Welcome to MittaAI
This is the community repository for MittaAI and SlothAI users. All code or examples here are covered by the [MIT software license](https://github.com/MittaAI/mitta-community/blob/main/LICENSE).

The SlothAI framework, which runs MittaAI, is located [here](https://github.com/MittaAI/SlothAI).

There is a [Discord server](https://discord.gg/SxwcVGQ8j9) available for help with building or running pipelines.

## Getting Started Video
Before you begin, we recommend watching the Getting Started video guide. This guide will help you become familiar with important concepts such as callbacks, storage, and how to use pipelines effectively.

 [![Getting Started...with Pirates](https://img.youtube.com/vi/CuALke2rQbQ/0.jpg)](https://www.youtube.com/watch?v=CuALke2rQbQ)

## Pipeline Cookbooks
In the [cookbooks directory](./cookbooks), you'll find a collection of example pipelines that are available for use on MittaAI's website. These pipelines can help you get started quickly. 

## Instructions for Use
### Creating a MittaAI Account
To use these pipelines, you'll need to create a [MittaAI account](https://mitta.ai) if you don't already have one. MittaAI provides a user-friendly platform for running and managing AI pipelines.

### Installing the SlothAI Framework (Optional)
If you prefer to use the pipelines locally on Google Cloud, you can install the [SlothAI framework](https://github.com/MittaAI/SlothAI). This framework allows you to run AI pipelines in your own environment.

### Storage Requirements
Mitta provides default database access to all accounts and provides table isolation to keep shared tables secure. For more avanced storage, you may elect to use a dedicated [FeatureBase Cloud](https://cloud.featurebase.com) account.

SlothAI will eventually support other database storage layers.

SlothAI and Mitta provide file storage via Google Cloud Storage.

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
If you have a pipeline you'd like to contribute, we welcome your contributions via a pull request (PR). To increase the likelihood of your PR being quickly added, please ensure the following:

1. Create a New Directory: Set up a new directory under the cookbooks section with a unique and concise name.
1. JSON Format: Ensure that the pipeline export file remains in JSON format.
1. Uniqueness and Simplicity: Make sure that the pipeline, node, and template names are unique and concise. Additionally, keep prompts, variables, comments, and other named objects reasonable and easy to understand.
1. Successful Execution: Verify that the pipeline runs successfully without errors.
1. README.md: Include a README.md file within the directory that provides clear instructions on how to use the pipeline. A well-documented pipeline enhances its usability.
1. Supporting Materials: If your contribution includes any supporting materials (e.g., documentation, examples, or additional files), organize them in a logical directory structure for ease of access and understanding.

By following these guidelines, you can contribute effectively and help maintain a high-quality collection of pipelines for the community. Your contributions are greatly appreciated!
