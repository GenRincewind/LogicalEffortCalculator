#!/usr/bin/env python3.6
import os
import uuid
from flask import Flask, flash, request, redirect, jsonify
from flask_cors import CORS
from capacitancejson import calculate_capacitance
UPLOAD_FOLDER = 'files'

app = Flask(__name__)
CORS(app)


@app.route('/')
def root():
    return '<h1>Test</h1>'


@app.route('/calculate_capacitance',  methods=['POST'])
def calculate_capacitance_route():
    content = request.json
    #return jsonify(dict(content))

    data=calculate_capacitance(dict(content))
    response = jsonify(data)
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response


