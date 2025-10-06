import time
import json
import uuid
from flask import Flask, request, Response, jsonify
from flask_cors import CORS
import re # <--- YOU MUST ADD THIS LINE

app = Flask(__name__)
CORS(app)

LOREM_IPSUM = """

*lol*

```
python3 main.py
```

![](https://media.istockphoto.com/id/1316134499/photo/a-concept-image-of-a-magnifying-glass-on-blue-background-with-a-word-example-zoom-inside-the.jpg?s=612x612&w=0&k=20&c=sZM5HlZvHFYnzjrhaStRpex43URlxg6wwJXff3BE9VA=)


las:

   - las

   - las

Lorem ipsum dolor sit amet, 

consectetur adipiscing elit, 

sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.


"""

@app.route('/upload', methods=['POST'])
def upload_file():
    """
    Mock file upload endpoint.
    It doesn't save the file, just simulates an upload process.
    """
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    # Simulate network/processing delay
    time.sleep(2)

    # Generate a unique filename and a mock S3 URL
    unique_id = uuid.uuid4()
    mock_s3_url = f"https://mock-s3-bucket.s3.amazonaws.com/{unique_id}/{file.filename}"

    return jsonify({'url': mock_s3_url})

@app.route('/chat', methods=['POST'])
def chat():
    request_data = request.json
    chat_id = request_data.get('chat_id')
    prompt = request_data.get('prompt')

    def generate_response():
        current_chat_id = chat_id if chat_id else str(uuid.uuid4())
        
        chat_id_payload = {'chat_id': current_chat_id}
        yield f"data: {json.dumps(chat_id_payload)}\n\n"
        time.sleep(0.1)

        # 1. Determine the base response text
        if "Image attached" in prompt:
            response_text = "I see you've attached an image. " + LOREM_IPSUM
        else:
            response_text = LOREM_IPSUM

        # 2. Pre-process the response text to replace newlines with <br> tags.
        # This is where the 're' module is used.
        text_with_breaks = re.sub(r'\n\n+', '<br> ', response_text.strip())
        
        # 3. Tokenize the modified text.
        words = text_with_breaks.split()

        for word in words:
            # Check if the word is the breakline tag
            if word == '<br>':
                token_payload = {'token': word}
            else:
                # For regular words, add a trailing space for separation
                token_payload = {'token': f"{word} "}
                
            yield f"data: {json.dumps(token_payload)}\n\n"
            time.sleep(0.05)
            
        done_payload = {'token': '[DONE]'}
        yield f"data: {json.dumps(done_payload)}\n\n"

    return Response(generate_response(), mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(port=5001, debug=True, threaded=True)
