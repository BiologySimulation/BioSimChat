from flask import Flask, request, jsonify, render_template
import requests
import os
from dotenv import load_dotenv
import google.generativeai as genai
import os
from flask_cors import CORS


# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

info = open('info.txt', 'r').read()
buttons = open('buttons.txt', 'r').read()

# Get API key from environment variables
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel("gemini-1.5-flash")

@app.route('/gemini-chat', methods=['POST'])
def gemini_chat():
    # Get the user prompt from the request
    data = request.get_json()
    userinput = data.get('userinput')

    try:

        prompt = f"""
        Using the information delimited by the triple backticks to help you answer the prompt delimited by the triple apostrophes. 
        Limit yourself to 5 sentences unless otherwise specified by the prompt. 
        If the prompt is not related to the topic of biological functions, respond with the response \"Sorry, I cannot help you with that\".
        
        ```{info}```

        '''{userinput}'''
        """

        # Replace the URL and structure based on Google's Gemini API docs
        response = model.generate_content(prompt)

        buttonprompt = f"""
        Using the prompt delimited by the triple apostrophes, choose one of the words within the triple backticks which represent some biological functions which is the most relevant to the prompt. 
        Your response should only include that word, and no additional words. If none of the words are relevant, your response should be "none".
        
        Do not respond with any word which is not in the list within the triple backticks, and respond with "none" instead if this is the case.
        Do not include any additional words, only include one word which is the word in the list.

        '''{prompt}'''

        ```{buttons}```


        """

        buttonresponse = model.generate_content(buttonprompt)
        print(buttonresponse.text)
        # Return the bot's reply to the frontend
        output = jsonify({"reply": response.text, "button": buttonresponse.text})
        return output

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"reply": "Sorry, there was an error processing your request.", "button": "none"}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')