# Vision to Speech Pipeline
This pipeline implements a vision to speech agent. Use it to describe the scene with spoken words.

Add the pipeline to [MittaAI](https://mitta.ai) from the `pipelines` page. To download or hear the audio file, use the output `uri` in the callback log. If you use the URL outside your browser, throw your [MittaAI token](https://mitta.ai/settings) on the end.

## Example
![Faraday](https://github.com/MittaAI/mitta-community/blob/main/cookbooks/visionspeech/experiment.png?raw=true)

[Audio](https://github.com/MittaAI/mitta-community/raw/main/cookbooks/visionspeech/complex-jackdaw-mitta-aispeech_0.mp3)

## Sample Output
```
{
  "filename": "DALLE_2023-12-01_18.48.58_-_Create_an_image_of_Michael_Faraday_in_a_19th-century_laboratory_during_the_day_surrounded_by_Victorian-era_scientific_equipment._Faraday_is_closely_o.png",
  "content_type": "image/png",
  "username": "annoying-shrew-of-expertise",
  "scene": [
    "This is an intricate and highly detailed image depicting a man in a vintage setting engaged in scientific work. He has a neatly groomed beard and mustache, and he's wearing a suit typical of the late 19th or early 20th century. His attention is focused on a glowing device that appears to be an experiment or a scientific apparatus with several shining tubes arrayed in a row. The setting suggests a laboratory or a study, with large windows and shelves filled with books in the background. An assortment of scientific equipment, like glassware and lamps producing a warm light, is arranged on the workbench, adding to the atmosphere of earnest inquiry and invention. The image has a sepia-toned, nostalgic feel, likely intended to evoke the era of early electrical experimentation."
  ],
  "assistant_content": "The image shows a man in a vintage setting, immersed in scientific work. He has a well-groomed beard and mustache, wearing a suit from the late 19th or early 20th century. His attention is focused on a glowing device, which seems to be an experiment or scientific apparatus with shining tubes in a row. It appears to be a laboratory or study, with large windows and shelves filled with books in the background. On the workbench, you can see various scientific equipment, like glassware and lamps emitting warm light. The overall sepia-toned image evokes a nostalgic feel, reminiscent of the era of early electrical experimentation.",
  "uri": [
    "https://mitta.ai/d/annoying-shrew-of-expertise/complex-jackdaw-mitta-aispeech_0.mp3?token="
  ],
  "callback_uri": "https://mitta.ai/annoying-shrew-of-expertise/callback?token=BLAT",
  "processor": "callback",
  "node_id": "QK7r7rlFk5EyZ",
  "pipe_id": "F3EsWCjFI3Iom"
}
```