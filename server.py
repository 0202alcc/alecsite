from flask import Flask, render_template, url_for, jsonify
import json

app = Flask(__name__)


# Load the hash map from the JSON file
def load_hash_map():
    try:
        with open('hash_map.json', 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"An error occurred while loading the hash map: {e}")
        return {}
    

@app.route('/')
# url_for('static', filename='style.css')
def home():
    hash_map = load_hash_map()
    return render_template("index.html", hash_map=hash_map)

@app.route('/about/')
def about():
    return render_template("about.html")

@app.route('/experience/')
def work():
    return render_template("work.html")

@app.route('/api/data')
def api_data():
    hash_map = load_hash_map()
    return jsonify(hash_map)

if __name__ == "__main__":
    app.run(debug=True)