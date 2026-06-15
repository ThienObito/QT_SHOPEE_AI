from flask import Flask, render_template, request, jsonify
from google import genai
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)

API_KEY = os.getenv("GEMINI_API_KEY")

client = genai.Client(
    api_key=API_KEY
)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():

    try:
        data = request.get_json()

        message = data.get("message", "")

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=message
        )

        return jsonify({
            "success": True,
            "answer": response.text
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "answer": str(e)
        })

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5001,
        debug=True,
        use_reloader=False
    )