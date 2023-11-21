import os
from os.path import join, dirname
from dotenv import load_dotenv

from flask import (
    Flask,redirect,url_for,
    render_template,request,
    jsonify)
from pymongo import MongoClient
import requests
import certifi
from bson import ObjectId

cert = certifi.where()

app = Flask(__name__)

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

MONGODB_URI = os.environ.get("MONGODB_URI")
DB_NAME =  os.environ.get("DB_NAME")

client = MongoClient(MONGODB_URI)

db = client[DB_NAME]

@app.route('/')
def main():
        words_result = db.words.find({}, {'_id': False})
        words = []
        for word in words_result:
                definition = word['definitions'][0]['shortdef']
                definition = definition if type(definition) is str else definition[0]
                words.append({
                        'word' : word['word'],
                        'definition': definition,
                })
        msg = request.args.get('msg')
        return render_template('index.html', words=words, msg=msg)
    
@app.route('/detail/<keyword>')
def detail(keyword):
        api_key = "232b5fa0-da77-43dd-aa09-cac79c58910c"
        url = f'https://www.dictionaryapi.com/api/v3/references/collegiate/json/{keyword}?key={api_key}'
        response = requests.get(url)
        definitions = response.json()

        if not definitions:
                return render_template('error.html', keyword=keyword, suggestions=[])

        if type(definitions[0]) is str:
                suggestions = ', '.join(definitions)
                return render_template('error.html', keyword=keyword, suggestions=suggestions)

        status = request.args.get('status_give', 'new')

        return render_template(
                'detail.html',
                word=keyword,
                definitions=definitions,
                status=status
        )

@app.route('/api/save_word', methods=['POST'])
def save_word():
        json_data = request.get_json()
        word = json_data.get('word_give')
        definitions = json_data.get('definitions_give')

        doc = {
                'word': word,
                'definitions': definitions,
        }

        db.words.insert_one(doc)

        return jsonify({
                'result': 'success',
                'msg': f'the word, {word}, was saved!!!',
        })


@app.route('/api/delete_word', methods=['POST'])
def delete_word():
        word = request.form.get('word_give')
        db.words.delete_one({'word' : word})
        db.examples.delete_many({'word' : word})
        return jsonify({
            'result' : 'success',
            'msg' : f'the word, {word}, was delete'
        })

@app.route('/api/get_exs', methods=['GET'])
def get_exs():
        word = request.args.get('word')
        example_data = db.examples.find({'word': word})
        examples = []
        for example in example_data:
                examples.append({
                        'example' : example.get('example'),
                        'id' : str(example.get('_id')),
                })
        return jsonify({
                'result': 'success',
                'examples' : examples
        })

@app.route('/api/save_ex', methods=['POST'])
def save_ex():
        word = request.form.get('word')
        example = request.form.get('example')
        doc = {
                'word': word,
                'example': example,
        }
        db.examples.insert_one(doc)
        return jsonify({
                'result': 'success',
                'msg': f'Your , {example}, for the word, {word}, was saved!',       
        })

from flask import request

@app.route('/api/delete_ex', methods=['POST'])
def delete_ex():
    id = request.form.get('id')  # Retrieve the 'id' from the request data
    word = request.form.get('word')
    db.examples.delete_one({'_id': ObjectId(id)})
    return jsonify({
        'result': 'success',
        'msg': f'Your word, {word}, was deleted!'
    })


if __name__ == '__main__':
    #DEBUG is SET to TRUE. CHANGE FOR PROD
    app.run(port=5000,debug=True)