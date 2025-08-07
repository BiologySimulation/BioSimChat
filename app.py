from flask import Flask, request, jsonify, render_template
import requests
import os
from dotenv import load_dotenv
import google.generativeai as genai
import os
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import json


# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app, resources={
    "/gemini-chat": {
        "origins": ["https://bio-sim.us", "http://bio-sim.us"]
    }
})

# Configure rate limiter
limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

info = open('info.txt', 'r').read()
buttons = json.load(open('buttons.json'))

# Get API key from environment variables
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel("gemini-2.0-flash")

@app.route('/gemini-chat', methods=['POST'])
@limiter.limit("10 per minute")
def gemini_chat():
    # Get the user prompt from the request
    data = request.get_json()
    userinput = data.get('userinput')

    try:

        prompt = f"""
        Answer the prompt delimited by the triple apostrophes in the best way possible using your knowledge about biology.
        When possible, incorporate information delimited by the triple backticks in your answer.

        Limit yourself to 5 sentences unless otherwise specified by the prompt. 

        When possible, make your answer a bulleted list, adding "<br><br>" after each line break. Do not bold any texts by wrapping the texts with **.
        Highlight any key/important words in your response. In order to highlight a text, wrap the text with <b> and </b>.
        Use "-" before each bullet point.

        If you are unable to respond to the prompt using either your knowledge about biology, or by using the information delimited by the triple backticks, 
        then add 'what is' in front of the prompt and then attempt to respond to it.
        
        If you still are unable to respond to the prompt, then respond with the response \"Sorry, I cannot help you with that\".
        
        ```{info}```

        '''{userinput}'''
        """

        # Replace the URL and structure based on Google's Gemini API docs
        response = model.generate_content(prompt)

        buttonprompt = f"""
        The given prompt is delimited by the triple apostrophes.
        The given Array is delimited by the triple backticks.

        Your task is to pick one of the strings in the Array which is the most relevant to the prompt.
        Your response should only include that string, and nothing else.
        If none of the keys in the JSON text are relevant to the prompt, your response should be "none".

        '''{userinput}'''

        ```{buttons.keys()}```


        """

        buttonresponse = model.generate_content(buttonprompt)
        buttonresponse = buttonresponse.text
        print(buttonresponse)
        # Return the bot's reply to the frontend
        if buttonresponse.endswith("\n"):
            buttonresponse = buttonresponse.removesuffix("\n")
        while buttonresponse.endswith(" "):
            buttonresponse = buttonresponse.removesuffix(" ")
        output = jsonify({"reply": response.text, "button": buttons[buttonresponse]})
        return output

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"reply": "Sorry, there was an error processing your request.", "button": "none"}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=443, ssl_context=('certificate.pem', 'private.pem'))