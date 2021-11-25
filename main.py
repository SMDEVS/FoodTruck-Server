from flask import Flask
from pymongo import MongoClient
from flask_bcrypt import Bcrypt
from decouple import config

username = config('USER')
password = config('PASSWORD')
database = config('DATABASE')

app = Flask(__name__)
bcrypt=Bcrypt(app)

cluster = MongoClient(
        host="mongodb+srv://{username}:{password}@cluster0.o3g7j.mongodb.net/{database}?retryWrites=true&w=majority",
        port=27017,
        serverSelectionTimeoutMS=1000)

@app.route('/')
def index():
    return 'Hello World'

if __name__ == '__main__':
    app.run(host='localhost', port=9874)   
