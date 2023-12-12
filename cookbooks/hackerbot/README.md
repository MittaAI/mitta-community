# HackerNews Bot
This pipeline is designed to fetch and process news stories from Hacker News API, convert documents to text, transform JSON data, and generate chat responses using AI. It enables users to automate the extraction and transformation of data from various sources and engage with their audience through generated chat content. 

It can be used with the [piratebot](https://github.com/MittaAI/mitta-community/blob/main/cookbooks/piratebot) cookbook to implement an agent that posts on Discord.

![pirate](https://mitta.ai/images/hn.png)

Add the pipeline in this directory to [MittaAI](https://mitta.ai) from the `pipelines` page. The pipeline retreives (50) stories from Algolia's HN search endpoint. 

The URL is defined in `extras`, but could be moved to the POST to the pipeline's endpoint.

## Example POST
The POST doesn't require any data, by default.
```
curl -X POST "https://mitta.ai/pipeline/VPMRR1OsoNkyG/task?token=<token>" \
-H "Content-Type: application/json" \
-d '{}'
```

## Sample Output
```
{
	"assistant_content": "Here's an interesting story from the list:  Title: 'New AI startup from the co-authors of the Original Transformers Paper' Link: [Essential AI](https://essential.ai/)  Description: Essential AI is a new startup founded by the co-authors of the original Transformers paper. Transformers are a type of deep learning model that has been widely successful in natural language processing tasks. With Essential AI, the team aims to build cutting-edge AI technologies and provide state-of-the-art solutions for various industry applications. The startup's website provides an overview of their vision and expertise, and it will be interesting to see the advancements they bring to the field of AI.  (Note: This post has received 8 points and has comments in the Hacker News thread.)"
}
```