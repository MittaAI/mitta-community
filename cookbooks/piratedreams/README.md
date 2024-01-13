# Pirate Dreams Cookbook
The Pirate Dreams cookbook provides a pipeline which synthesizes a story using a chat processor. It then extracts objects from the story using a dictionary extraction processor, and passes the objects and the story into an image generation processor.

 ## Installation
 1. *MittaAI Account*: Ensure you have an active account on [MittaAI](https://mitta.ai).
 2. *Adding the Pipeline*: On the MittaAI platform, navigate to the `pipelines` section and add the Pirate Dreams pipeline using the provided `pipeline_dreams.json` file. You can download the file from [this link](https://github.com/MittaAI/mitta-community/blob/main/cookbooks/piratedreams/pipeline_dreams.json?raw=true).

 ## Video Guide
 For a comprehensive guide on how to set up and use the Pirate Dreams pipeline, watch our detailed video that covers building and using the pipeline.

 [![Getting Started...with Pirates](https://img.youtube.com/vi/CuALke2rQbQ/0.jpg)](https://www.youtube.com/watch?v=CuALke2rQbQ)

 ## Usage
 To initiate the pipeline, send a POST request as follows:

*From a terminal shell*:
 ```
 curl -X POST "https://mitta.ai/pipeline/<pipeline_id>/task?token=<your_token>" \
-H "Content-Type: application/json" \
-d '{"words": ["Welcome to my island, Mr. Pirate!""]}'
```

*Sample Output*:
```
The pirate, standing tall on his ship's deck, addresses a native of the island. The pirate ship, a magnificent vessel, is visible in the background, its wooden frame weathered by countless adventures on the high seas. In the native's hands, a plump coconut glistens under the sun's golden rays.  With a hearty voice, the pirate exclaims, 'Arr! Well, ahoy there, ye native scallywag! Ye've got a keen eye for ships, I'll give ye that. Me vessel be a beauty indeed, sturdy and strong like a true pirate ship should be, aye!' Grinning mischievously, he eagerly accepts the native's kind offer of a coconut, outstretching his rough palm to receive it.
```

![Dreams](https://github.com/MittaAI/mitta-community/blob/main/cookbooks/piratedreams/05mjRjlgp8I2g9xE.png?raw=true)
