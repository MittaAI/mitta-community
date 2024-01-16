# Translate Webpage Bot
This pair of pipelines crawls a website visually and then translates the page contents into the language of your choice. It uses the Google `gemini-pro` model, but can be changed to use any model supported on the system, which itself supports tranlation to the desired language.

## Install
Add the two pipelines in this directory to [MittaAI](https://mitta.ai) from the `pipelines` page. One pipeline crawls the page, the other pipeline uses the image from that crawl to extract the text and translate it. 

If you use the `gemini-pro` model, you will need a [Gemini API token](https://makersuite.google.com/app/apikey).

You will be prompted for the `gemini-token` when you import the `translate` pipeline. To set the language, edit the `aichat` node in the pipeline after import. You will be prompted for the language and may set it to another value from the node detail page later.

The crawl is kicked off by sending a URL (URI) to the crawl endpoint.

## Use
### Example POST
The POST contains the URI to crawl.
```
curl -X POST "https://mitta.ai/pipeline/<pipe_id>/task?token=<token>" \
-H "Content-Type: application/json" \
-d '{"uri": "https://news.ycombinator.com/item?id=38989832"}'
```

### Sample Output
```
{
	"assistant_content": "2. Traducciu00f3n al espau00f1ol:  ''' [['Y Hacker News nuevo | pasado | comentarios | preguntar | mostrar | empleos | enviar u25b2 Muchos sitios web estu00e1n traducidos por mu00e1quinas: informaciu00f3n sobre paralelismo multidireccional (arxiv.org) 67 puntos por yorwba hace 10 horas | ocultar | pasado | favorito | 37 comentarios au00f1adir comentario u25b2 pif hace 1 hora | siguiente [-] u00a1Odio la forma en que las traducciones automu00e1ticas se tratan en la web como si fueran traducciones respetables, proporcionadas por profesionales! Puedo leer tres idiomas y me gustaru00eda que mi navegador eligiera la versiu00f3n 'principal' de una pu00e1gina si estu00e1 en alguno de esos tres idiomas, y solo recurrir a las traducidas si es necesario. u00a1Pero no hay forma de obtener este comportamiento! Y me gustaru00eda mucho que Google me sirviera las pu00e1ginas de Wikipedia en italiano o francu00e9s si el tema se refiere a Italia o Francia, y solo recurrir al inglu00e9s como alternativa, u00a1pero de nuevo no hay forma! Si configuro mi idioma principal en algo distinto del inglu00e9s, siempre obtendru00e9 documentaciu00f3n de MSDN mal traducida y una navegaciu00f3n web fea en general. Por lo tanto, estoy atascado con tu00edtulos de videos de YouTube mal traducidos y Wikipedia en inglu00e9s cuando busco un monumento en mi ciudad natal. responder u25b2 yorwba hace 23 minutos | padre | siguiente [-] En teoru00eda, el encabezado Accept-Language deberu00eda ser suficiente para obtener el comportamiento que deseas, pero por supuesto eso requiere que cada servidor implemente soporte, por lo que en la pru00e1ctica muchos sitios seguiru00e1n redirigiu00e9ndote a una versiu00f3n diferente segu00fan la geolocalizaciu00f3n de IP. Pero las etiquetas <link rel='alternate' hreflang='...' href='...'/> son bastante comunes para SEO, asu00ed que tal vez una extensiu00f3n podru00eda analizarlas para verificar si preferiru00edas una de las otras versiones. responder. u25b2 bluetomcat hace <snip>"
}
```

If you have issues configuring the pipeline, pop into [Discord](https://discord.com/invite/SxwcVGQ8j9).