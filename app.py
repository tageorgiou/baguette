import os
import json
import base64

from flask import Flask, request, redirect
from mongokit import Connection, Document

OAUTH_URL = 'https://www.facebook.com/dialog/oauth?client_id=%s&redirect_uri=%s'
FB_APP_ID = 196886180398409
FB_DOMAIN = 'https://baguette.herokuapp.com/'

app = Flask(__name__)
app.debug = True


# Page unauthenticated users land at.
@app.route('/start', methods=['GET', 'POST'])
def start():
    return redirect(OAUTH_URL % (FB_APP_ID, FB_DOMAIN))

@app.route('/', methods=['POST'])
def main():
    signed_req_raw = base64.b64decode(request.form.get('signed_request', ''))
    if not signed_req_raw:
        return '', 400
    signed_req = json.parse(signed_req_raw)
    raise
    return 'welcome'

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
