from flask import Flask, render_template
app = Flask(__name__)




# Register the blueprints with the Flask app
@app.route('/')
def index():
    return render_template('index.html')










app.run(port="8080")