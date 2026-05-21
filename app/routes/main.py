from flask import Blueprint, render_template

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/about')
def about():
    return render_template('about.html')

@main_bp.route('/services')
def services():
    return render_template('services.html')

@main_bp.route('/contact')
def contact():
    return render_template('contact.html')

@main_bp.route('/portfolio')
def portfolio():
    return render_template('portfolio.html')

@main_bp.route('/blog')
def blog():
    return render_template('blog.html')

@main_bp.route('/activities')
def activities():
    return render_template('activities.html')

@main_bp.route('/faq')
def faq():
    return render_template('faq.html')

@main_bp.route('/pricing')
def pricing():
    return render_template('pricing.html')

@main_bp.route('/signup')
def signup():
    return render_template('signup.html')

@main_bp.route('/donate')
def donate():
    return render_template('donate.html')
