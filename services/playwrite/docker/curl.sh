curl -X POST http://localhost:5000/grub2 \
     -H "Content-Type: application/json" \
     -d '{
           "grub_token": "f00bar",
           "username": "hilarious-quetzal-of-excitement",
           "query": "crawl mitta.ai",
           "callback_url": "https://kordless.ngrok.io/hilarious-quetzal-of-excitement/callback?token=g7q5V1SZ74MWudzO_INnIxvlpKxB4oAVyXF46a",
           "openai_token": "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"
         }'