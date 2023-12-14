# Visualize Pipeline
This pipeline is designed to process and transform image and text data using AI processors. It can generate scene descriptions, convert text into pirate thoughts, and create images based on input text. The pipeline also includes a callback node for handling callback requests.

It can be used with the [piratebot](https://github.com/MittaAI/mitta-community/blob/main/cookbooks/piratebot) cookbook to implement an agent that posts on Discord.

## Sample Image
<img src="https://raw.githubusercontent.com/MittaAI/mitta-community/main/cookbooks/visualize/chest.png" width="313">

Video guide coming soon!

## Install
You will need both an [OpenAI token](https://platform.openai.com/api-keys) as well as a [Gemini token](https://makersuite.google.com/app/apikey).

Add the pipeline in this directory to [MittaAI](https://mitta.ai) from the `pipelines` page. The pipeline retreives (50) stories from Algolia's HN search endpoint. 

The URL is defined in `extras`, but could be moved to the POST to the pipeline's endpoint.

## Use
### Upload an image.
Navigate to the pipeline in your Mitta account. Click 'upload' to upload an image. The image will be sent to Gemini for scene exraction, then an `aichat` processor will build a scene description. The final node calls OpenAI dalle-3 to generate a new image.

### Sample Output
```
{"scene": [
" The image contains a cartoon beaver holding a chainsaw. The beaver is standing in a forest, and there is a pile of logs behind it. The beaver is smiling and has its teeth bared. It is wearing a plaid shirt."
],
"assistant_content": [
"Arr, shiver me timbers, what be this? Me eyes do behold a beach, with coconut trees swayin' in the breeze and sand stretchin' as far as the eye can see. But what be this I spy? A chest, locked tight, its treasure waitin' to be plundered.  Me heart be racin' with excitement, me mind conjurin' up visions of what riches might lie within. Jewels, gold coins, and treasures beyond me wildest dreams. But as me gaze shifts, me eyes fall upon a peculiar sight.  A beaver, standin' tall and proud in the midst of a forest, a chainsaw clutched firmly in its furry paws. Its teeth be bared in a mischievous grin, and it be wearin' a plaid shirt, the very picture of a lumberjack.  Me mind be abuzz with wonder, tryin' to fathom the mysteries of this unlikely encounter. What be a beaver doin' in the middle of a pirate's adventure? And why be it brandishin' such a fearsome weapon?  Could it be a guardian of the treasure, a protector of the hidden riches? Or perhaps it be a fellow pirate, a master of disguise, ready to join me on me quest for plunder?  Me curiosity be piqued, me instincts tellin' me that this beaver be more than it seems. As I ponder the possibilities, I feel a surge of excitement, me heart poundin' with anticipation.  Whatever secrets await me, one thing be for certain: this encounter with the chainsaw-wieldin' beaver be sure to leave its mark on me piratin' soul."
],
"uri": [
[
https://oaidalleapiprodscus.blob.core.windows.net/private/org-Kg1s7HQV0Fj2aigpiOSZjB4c/user-lf9bOPRo0mCmyR3VO6VFZ6rW/img-o5RZjuT6rBJYtOOyv2CHZfVa.png?st=2023-12-14T15%3A24%3A27Z&se=2023-12-14T17%3A24%3A27Z&sp=r&sv=2021-08-06&sr=b&rscd=inline&rsct=image/png&skoid=6aaadede-4fb3-4698-a8f6-684d7786b067&sktid=a48cca56-e6da-484e-a814-9c849652bcb3&skt=2023-12-14T15%3A53%3A17Z&ske=2023-12-15T15%3A53%3A17Z&sks=b&skv=2021-08-06&sig=/T3q0tlO6W5OSKp9iYtavnTDeVgww4gormZxxK066pA%3D
]
]}
```

If you have issues configuring the pipeline, pop into [Discord](https://discord.com/invite/SxwcVGQ8j9).