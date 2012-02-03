import os
import json
from flask import Flask, request, redirect
from mongokit import Connection, Document
from database import db

OAUTH_URL = 'https://www.facebook.com/dialog/oauth?client_id=%s&redirect_uri=%s'
FB_APP_ID = 196886180398409
FB_DOMAIN = 'https://baguette.herokuapp.com/'

app = Flask(__name__)
app.debug = True


# Page unauthenticated users land at.
@app.route('/start', methods=['GET', 'POST'])
def start():
    return redirect(OAUTH_URL % (FB_APP_ID, FB_DOMAIN))

@app.route('/class/<classname>')
def show_class(classname):
    cl = db.classes.find_one({'name': classname})
    if cl == None:
        return "404"
    else:
        return str(cl)

@app.route('/', methods=['POST'])
def main():
    signed_req_raw = request.form.get('signed_request', None)
    if not signed_req_raw:
        return '', 400
    signed_req = json.parse(signed_req_raw)
    raise
    return 'welcome'

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
