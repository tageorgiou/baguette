import os
from flask import Flask, request

app = Flask(__name__)
app.debug = True

@app.route('/', methods=['GET','POST'])
def hello():
    raise
    return 'Hello world!!'

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
