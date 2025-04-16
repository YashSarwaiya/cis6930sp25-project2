from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/resolve_coref", methods=["POST"])
def resolve_coref():
    data = request.get_json()
    text = data.get("text", "")

    # A dummy response for demonstration
    # You can modify the text logic here to mock different responses
    response = {
        "coreference_mapping": [
            {"0": "Rick", "2": "he"},
            {"5": "Mary", "7": "She"}
        ]
    }
    return jsonify(response)

if __name__ == "__main__":
    app.run(host="localhost", port=65535)
