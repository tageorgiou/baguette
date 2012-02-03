import os
from flask import Flask

from mongokit import Connection, Document

app = Flask(__name__)

#MLU = 'mongodb://heroku_app2744761:7j7n2hpdftkrumvl1uhf7k41k8@ds029847.mongolab.com:29847/heroku_app2744761'
#
#connection = Connection(MLU)
#db = connection.heroku_app2744761

@app.route('/', methods=['GET','POST'])
def hello():
    print request.form
    return 'Hello world!!'

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
