from flask import Flask, render_template, url_for

app = Flask(__name__)
@app.route('/')
# url_for('static', filename='style.css')
def home():
    return render_template("home.html")

@app.route('/about/')
def about():
    return render_template("about.html")

@app.route('/experience/')
def work():
    return render_template("work.html")


if __name__ == "__main__":
    app.run(debug=True)