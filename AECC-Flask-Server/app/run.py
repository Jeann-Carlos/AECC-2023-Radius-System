from flask import Flask, render_template, request
from RegisterValidation import validate_with_google_sheets
from AeccPiholeCursor import getMac,driverProgram,addToTable

app = Flask(__name__)




# Register the blueprints with the Flask app
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/services')
def services():
    return render_template('services.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/portfolio')
def portfolio():
    return render_template('porftolio.html')
@app.route('/blog')
def blog():
    # Your blog page logic here
    return render_template('blog.html')

@app.route('/activities')
def activities():
    # Your activities page logic here
    return render_template('activities.html')

@app.route('/faq')
def faq():
    # Your FAQ page logic here
    return render_template('faq.html')

@app.route('/pricing')
def pricing():
    return render_template('pricing.html')


@app.route('/signup')
def signup():
    return render_template("signup.html")

@app.route('/donate')
def donate():
    return render_template("donate.html")

@app.route('/link_your_device', methods=['GET', 'POST'])
def link_your_device():
    error=""
    if request.method == 'POST':
        student_id = request.form['student_id']
        telephone = request.form['telephone']
        if validate_with_google_sheets(student_id, telephone):
            user_ip = request.remote_addr
            mac_address = getMac(user_ip)
            if not mac_address==-1:
                addToTable(mac_address)
            exit_value = driverProgram()
            error = "Mac address not found"
        else:
            error =  "User or password invalid"
    return render_template('link_your_device.html',error=error)




app.run(port="8080")