from flask import Flask
import os

app = Flask(__name__)
print("Current working directory:", os.getcwd())
print("Templates exist:", os.path.exists(os.path.join(app.root_path, 'templates', 'index.html')))
print(os.listdir(app.root_path))
