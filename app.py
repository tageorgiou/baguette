import os
import json
import base64

from flask import Flask, request, redirect
from database import db, User

OAUTH_URL = 'https://www.facebook.com/dialog/oauth?client_id=%s&redirect_uri=%s'
FB_APP_ID = 196886180398409
FB_DOMAIN = 'https://baguette.herokuapp.com/'

app = Flask(__name__)
app.debug = True

def base64_url_decode(inp):
    padding_factor = (4 - len(inp) % 4) % 4
    inp += "="*padding_factor 
    return base64.b64decode(unicode(inp).translate(dict(zip(map(ord, u'-_'), u'+/'))))


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
    signed_req_raw = base64_url_decode(unicode(request.form.get('signed_request', '')))
    if not signed_req_raw:
        return '', 400
    signed_req = json.parse(signed_req_raw)
    fb_id = signed_req['user_id']
    oauth_token = signed_req['auth_token']
    user = User()
    user['fb_id'] = fb_id
    user['oauth_token'] = oauth_token
    user.save()
    return 'welcome'

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
