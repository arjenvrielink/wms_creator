#!/usr/bin/env python
from flask import Flask, render_template, url_for, request, redirect
from gingerdb import Config, GingerDB, MaatregelAfweging

app = Flask(__name__)
app.debug = True

config = Config()
db = GingerDB(config) 
ma = MaatregelAfweging(db)

@app.route('/')
def index():
	return render_template('index.html', result="")

@app.route('/mgt/', methods=['POST'])
def maatgevendtraject():
	error = None
	if request.method == 'POST':
		zoekstraal = int(request.form['zoekstraal'])
        ma.maatgevendtraject(zoekstraal)
        result = 'ok'

	return render_template('index.html', result=result)
	#return redirect('/')

if __name__ == "__main__":
	app.debug = True
	app.run('0.0.0.0')
