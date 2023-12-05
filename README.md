# Welcome to MittaAI
This is the community repository for MittaAI and SlothAI users. All code or examples here are covered by the [MIT software license](https://github.com/MittaAI/mitta-community/blob/main/LICENSE).

The SlothAI framework, which runs MittaAI, is located [here](https://github.com/kordless/SlothAI).

There is a [Discord server](https://discord.gg/SxwcVGQ8j9) available for help with building or running pipelines.

## Contributing
If you have a pipeline you'd like to contribute, please do a PR for it.

The PR will be more likely to be added quickly if the following is true:
1. A new directory under `cookbooks` with a unique, short and polite name.
2. The pipeline export file should remain JSON formatted.
3. Pipeline, node and template names should be unique, short and polite.
4. Prompts, variables, comments and other named objects should be reasonable.
5. The pipeline runs successfully.
5. A `README.md` file that clearly and politely explains how to use the pipeline.
6. Any supporting materials, organzied by reasonable directory structure.

## Getting Started Video
Be sure to watch the getting started video guide. This guide will famialrize you with callbacks, storage and pipeline use.

[![Getting Started](https://img.youtube.com/vi/ntLqz38hC60/0.jpg)](https://www.youtube.com/watch?v=ntLqz38hC60)

## Pipeline Cookbooks
The [cookbooks directory](./cookbooks) contains the example pipelines available for use on [MittaAI](https://mitta.ai)'s website.

## Instructions for Use
To use pipelines here, you will either need to create a [MittaAI account](https://mitta.ai), or install the [SlothAI framework](https://github.com/kordless/SlothAI) on Google Cloud.

For now, you will need a [FeatureBase Cloud](https://cloud.featurebase.com) account if you use a pipeline that needs storage.

SlothAI will eventually support other database storage layers.

### Importing a Pipeline
To import a pipeline, navigate to the `pipelines` tab and click `import`. Choose the pipeline you would like to import and then fill in any extras when prompted.

