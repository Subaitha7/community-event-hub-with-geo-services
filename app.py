from flask import Flask, render_template, redirect, url_for

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    # Implement your login logic or render login template
    return "Login Page (to be implemented)"

@app.route('/signup')
def signup():
    # Implement your signup logic or render signup template
    return "Signup Page (to be implemented)"

if __name__ == '__main__':
    app.run(debug=True)
