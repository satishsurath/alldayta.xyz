import os
import openai
from app import app
from flask import render_template, flash, redirect, url_for
from flask_wtf.csrf import generate_csrf


# -------------------- Flask app configurations --------------------

openai.api_key = os.getenv("OPENAI_API_KEY")

# -------------------- Routes --------------------
@app.route('/')
@app.route('/index')
def index():
  return render_template('index.html')

@app.route('/privacy-policy')
def privacypolicy():
    return render_template('privacy.html')
