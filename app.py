import base64
import hashlib
import hmac
import httplib2
import json
import os

from flask import Flask, request, redirect, render_template
from database import db, User

OAUTH_URL = 'https://www.facebook.com/dialog/oauth?client_id=%s&redirect_uri=%s'
TOKEN_ENDPOINT = 'https://graph.facebook.com/oauth/access_token?client_id=%s&redirect_uri=%s&client_secret=%s&code=%s'
FB_APP_ID = 196886180398409
FB_APP_SECRET = '3c8ac9932be4a87c132751ee8f9ee804'
FB_DOMAIN = 'https://baguette.herokuapp.com/'

app = Flask(__name__)
app.debug = True

def base64_url_decode(inp):
    padding_factor = (4 - len(inp) % 4) % 4
    inp += "="*padding_factor 
    return base64.b64decode(unicode(inp).translate(dict(zip(map(ord, u'-_'), u'+/'))))

def parse_signed_request(signed_request, secret):

    l = signed_request.split('.', 2)
    encoded_sig = l[0]
    payload = l[1]

    sig = base64_url_decode(encoded_sig)
    data = json.loads(base64_url_decode(payload))

    if data.get('algorithm').upper() != 'HMAC-SHA256':
        return None
    else:
        expected_sig = hmac.new(secret, msg=payload, digestmod=hashlib.sha256).digest()

    if sig != expected_sig:
        return None
    else:
        return data

@app.route('/class/<classname>')
def show_class(classname):
    cl = db.classes.find_one({'name': classname})
    if cl == None:
        return "404", 404
    else:
        return render_template('class.html', cl=cl)

@app.route('/', methods=['GET', 'POST'])
def main():
    if 'code' not in request.args:
        return redirect(OAUTH_URL % (FB_APP_ID, FB_DOMAIN))
    code = request.args.get('code', None)
    h = httplib2.Http()
    resp, content = h.request(TOKEN_ENDPOINT % (FB_APP_ID, FB_DOMAIN+"user", FB_APP_SECRET, code))
    if resp['status'] != 200:
        return content, 500
    return content

#    signed_req_raw = request.form.get('signed_request', '')
#    if not signed_req_raw:
#        return '', 400
#    signed_req = parse_signed_request(signed_req_raw, FB_APP_SECRET)
#    if 'fb_id' not in signed_req:
#    else:
#        user = db.users.User()
#        user['fb_id'] = signed_req['user_id']
#        user['oauth_token'] = signed_req['oauth_token']
#        user.save()
#        return 'welcome'

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
