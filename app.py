import base64
import hashlib
import hmac
import httplib2
import json
import os
import urlparse
from urllib import urlencode
import re
from werkzeug.contrib.cache import SimpleCache
cache = SimpleCache()
import datetime

from flask import Flask, request, redirect, render_template, session
from database import db

FB_APP_ID = 196886180398409
FB_APP_SECRET = '3c8ac9932be4a87c132751ee8f9ee804'
FB_DOMAIN = 'https://baguette.herokuapp.com/'
UNSECURE_DOMAIN = 'http://baguette.herokuapp.com/'
OAUTH_URL = 'https://www.facebook.com/dialog/oauth?client_id=%s&redirect_uri=%s&scope=publish_actions'
TOKEN_ENDPOINT = 'https://graph.facebook.com/oauth/access_token?client_id=%s&redirect_uri=%s&client_secret=%s&code=%s'
ME_URL = "https://graph.facebook.com/me?access_token=%s"
FBID_USER_URL = "https://graph.facebook.com/%s"
NOACTION_CLASS_TAKE = '-1'
BYPASS = False

app = Flask(__name__)
#app.debug = True
app.secret_key = '\x98_M\xcaAV\x19\xfe\x01""\xf6|\xf4\xe4\x18\xc6\xbb^\x93\x8e\x13\x0f\xe5'


def getUserProfile(fbid):
    """Return an fbid's user profile"""
    user_profile = cache.get('user_profile_' + str(fbid))
    if user_profile is not None:
        return user_profile
    
    url = FBID_USER_URL % fbid
    h = httplib2.Http()
    resp, content = h.request(url, "GET", '')
    was_successful = (resp['status'] == '200')
    if was_successful:
        user_profile = json.loads(content)
        cache.set('user_profile_' + str(fbid), user_profile, 15*60) #15min
        return user_profile
    else:
        raise Exception("Error getting user profile")

@app.route('/class/<classname>')
def show_class(classname):
    cl = db.classes.Class.find_one({'name': classname})
    fbid = ''
    if 'fb_id' in session:
        fbid = session['fb_id']
    if cl == None:
        return "404", 404 #Better 404 page
    cl_is_taking = fbid in cl['users'] #Am I taking the class?
    if BYPASS or fbid == '':
        friendList = []
    else:
        friendList = get_friends()
    classTakers = cl['userlist']
    friendClassTakers = []
    for f in friendList:
        if unicode(f['uid']) in classTakers:
            friendClassTakers.append(f)
    schedule = makeClassSchedule(cl)
    if fbid in cl['usersessions']:
        mySessions = cl['usersessions'][unicode(fbid)]
    else:
        mySessions = []
    return render_template('class.html', cl=cl, fbid=fbid,
            cl_is_taking=cl_is_taking, friends=friendClassTakers,
            schedule=schedule, mySessions=mySessions)

def findFirstSessionType(cl, stype):
    for s in cl['sessions']:
        if s['type'] == unicode(stype):
            return s

def takeClass(cl, fbid):
    """ Given a class and fbid for user, take the class"""
    url = 'https://graph.facebook.com/me/mitcourses:take?'
    if BYPASS:
        accesstoken = ""
    else:
        if 'token' not in session:
            raise Exception
        accesstoken = session['token']
    classurl = urlencode({'class': UNSECURE_DOMAIN + 'class/' + cl['name'],
        'access_token': accesstoken,
        'professor' : ', '.join(cl['professor']),
        'start_time' : datetime.datetime.now().isoformat(),
        'end_time':    '2012-12-22 00:00:00'})
    url = url + classurl
    h = httplib2.Http()
    if BYPASS:
        was_successful = False
    else:
        resp, content = h.request(url, "POST", '')
        print 'requesting, ' + url
        was_successful = (resp['status'] == '200')
        #print 'was_succesful, ' + was_successful
        content = json.loads(content)
        print 'content, ' + str(content)
    if was_successful:
        cl['users'][fbid] = unicode(content['id'])
    else: 
        cl['users'][fbid] = NOACTION_CLASS_TAKE
    cl['userlist'].append(fbid)

    #prepopulate initial session choices
    if fbid not in cl['usersessions']:
        cl['usersessions'][fbid] = []
    firstLecture = findFirstSessionType(cl, 'lecture')
    if firstLecture is not None:
        print firstLecture
        cl['usersessions'][fbid].append(firstLecture['label'])
    firstLab = findFirstSessionType(cl, 'lab')
    if firstLab is not None:
        cl['usersessions'][fbid].append(firstLab['label'])
    firstRecitation = findFirstSessionType(cl, 'recitation')
    if firstRecitation is not None:
        cl['usersessions'][fbid].append(firstRecitation['label'])

    db.classes.save(cl)
    return ""

@app.route('/class/<classname>/take')
def take_class(classname):
    cl = db.classes.Class.find_one({'name': classname})
    if cl == None:
        return "404", 404
    if 'fb_id' not in session:
        #get authorization
        session['redirect_next'] = '/class/%s/take' % classname
        return redirect('/')
        #return "not authorized"
    if 'token' not in session:
        return "not logged in"
    fbid = session['fb_id']
    dbg = takeClass(cl, fbid)
    #TODO: flash this?
#    return 'yay. you are now taking %s %s' % (classname, dbg)
    return redirect('/class/%s' % classname)

def untakeClass(cl, fbid):
    url = 'https://graph.facebook.com/%s?'
    if BYPASS:
        accesstoken = ""
    else:
        if 'token' not in session:
            raise Exception
        accesstoken = session['token']
    classurl = urlencode({'access_token' : accesstoken})
    if fbid not in cl['users']:
        return "Um, you aren't taking this class"
    actionid = cl['users'][fbid]
    if actionid == NOACTION_CLASS_TAKE:
        if fbid in cl['users']:
            del cl['users'][fbid]
            cl['userlist'].remove(fbid)
            if fbid in cl['usersessions']:
                del cl['usersessions'][fbid]
            db.classes.save(cl)
        return "Not taking"
    else:
        url = (url % actionid ) + classurl
        h = httplib2.Http()
        resp, content = h.request(url, "DELETE", '')
        was_successful = (resp['status'] == '200')
        if was_successful:
            if fbid in cl['users']:
                del cl['users'][fbid]
                cl['userlist'].remove(fbid)
                if fbid in cl['usersessions']:
                    del cl['usersessions'][fbid]
                db.classes.save(cl)
    return ""

@app.route('/class/<classname>/untake')
def untake_class(classname):
    cl = db.classes.Class.find_one({'name': classname})
    if cl == None:
        return "404", 404
    if 'fb_id' not in session:
        return "not authorized"
    if 'token' not in session:
        return "not logged in"
    fbid = session['fb_id']
    dbg = untakeClass(cl, fbid)
    #return 'yay. you are now not taking %s %s' % (classname, dbg)
    return redirect('/class/%s' % classname)

@app.route('/class/<classname>/<sessionname>/take')
def take_session(classname, sessionname):
    cl = db.classes.Class.find_one({'name': classname})
    fbid = session['fb_id']
    if fbid in cl['usersessions']:
        cl['usersessions'][fbid].append(sessionname)
    else:
        cl['usersessions'][fbid] = [sessionname]
    cl.save()
    return redirect('/class/%s' % classname)

@app.route('/class/<classname>/<sessionname>/untake')
def untake_session(classname, sessionname):
    cl = db.classes.Class.find_one({'name': classname})
    fbid = session['fb_id']
    cl['usersessions'][fbid].remove(sessionname)
    cl.save()
    return redirect('/class/%s' % classname)

def find_registered_classes(fbid):
    """What classes am I in?"""
    classes = []
    clcc = db.classes.Class.find({ 'userlist': unicode(fbid) })
    for i in range(0,clcc.count()):
        classes.append(clcc.next())
    return classes

def get_friends():
    """Return my friends list"""
    if 'fb_id' not in session:
        raise Exception()
    if 'token' not in session:
        raise Exception()
    authtoken = session['token']
    fbid = session['fb_id']

    friendsList = cache.get('friends_' + str(fbid))
    if friendsList is not None:
        return friendsList

    url = 'https://graph.facebook.com/fql?'
    endurl = urlencode({'access_token' : authtoken,
        'q': 'SELECT uid, name, pic_square FROM user WHERE uid = me() OR uid IN (SELECT uid2 FROM friend WHERE uid1 = me())'})
    url = url + endurl
    h = httplib2.Http()
    resp, content = h.request(url, "GET", '')
    was_successful = (resp['status'] == '200')
    if was_successful:
        friendsList = json.loads(content)['data']
        cache.set('friends_' + str(fbid), friendsList, 15*60) #15min
        return friendsList
    else:
        raise Exception("Need to login")

@app.route('/search')
def search():
    """Redirect to a class web page"""
    if 'q' not in request.args:
        return "No query specified"
    query = request.args['q']
    return redirect('/class/%s' % query)

@app.route('/autocomplete')
def autocomplete():
    """Autocomplete search box backend"""
    if 'term' not in request.args:
        return "No query specified"
    query = re.escape(request.args['term'])
    print query
    results = []
    mongoquery = {'$or' : [
        {'professor': {'$regex': query, '$options': 'i'}}, #case insensitive
        {'name': {'$regex': '^' + query, '$options': 'i'}},
        ]}

    for c in db.classes.Class.find(mongoquery).sort(u'name', 1).limit(10):
        labelHtml = '<span style="font-weight:bold">%s</span><span style="float:right">%s</span>' % \
            (c['name'], c['label'])
        val = {'label': labelHtml,
                'value': c['name'],
                'title': 'tttt',
                }
        results.append(val)
    print results
    return json.dumps(results)


def getMyProfile(access_token):
    """Return my profile"""
    h = httplib2.Http()
    resp, content = h.request(ME_URL % access_token)
    my_profile = json.loads(content)
    return my_profile

@app.route('/', methods=['GET', 'POST'])
def main():
    fb_id = 1111
    friends = []
    first_name='Thomas'
    classes = []
    if not BYPASS:
        if 'code' not in request.args:
            return redirect(OAUTH_URL % (FB_APP_ID, FB_DOMAIN))
            pass
        code = request.args.get('code')#,
#            'AQDOlT2Geph7__LHHi3VOyePP4kzTQ-i_VHbgA381AtDV5Np3tzkakHBOFiDokSwaRImkaB-n9qzo8T6f5Q6_lauY5ZSoRu_by997UL8QiLm6_Oof36ztB4lLa9bPfZuoyWr4vu-ixQEUOecVfXEs8uwNZRjc3fOyjP9MqF_bICuyUfUgzJKWnZ-Sdc-hwLC108#_=_')
        h = httplib2.Http()
        url = TOKEN_ENDPOINT % (FB_APP_ID, FB_DOMAIN, FB_APP_SECRET, code)
  
        resp, content = h.request(url)
        if resp['status'] != '200':
            return "Error requesting token.", 500
        param = urlparse.parse_qs(content)
        access_token, expires = [x[0] for x in param.values()]

        my_profile = getMyProfile(access_token)
        fb_id = my_profile['id']
        first_name = my_profile['first_name']

        user = db.users.find_one({'fb_id': unicode(fb_id)})
        created = 'Updated existing'
        if user is None:
            created = 'Created new'
            user = db.users.User()
            user['token'] = unicode(access_token)
            user['fb_id'] = fb_id
            user.save()
        else:
            user['token'] = unicode(access_token)
            user['fb_id'] = fb_id
            db.users.save(user)
        session['fb_id'] = fb_id
        session['token'] = access_token
        session['first_name'] = first_name
        #redirect to previoused page after getting auth
        if 'redirect_next' in session:
            redirect_next = session['redirect_next']
            del session['redirect_next']
            return redirect(redirect_next)
        baguette_friends = cache.get('baguette_friends_' + str(fb_id))
        if baguette_friends is None:
            friends = get_friends()
            baguette_friends = []
            userFBIDs = set()
            for u in db.users.User.find():
                userFBIDs.add(u['fb_id'])
            for f in sorted(friends, key=lambda f: f['name']):
                if unicode(f['uid']) in userFBIDs:
                    baguette_friends.append(f)
            
            cache.set('baguette_friends_' + str(fb_id), baguette_friends, 5*60)
            #5min
    else:
        pass

    return render_template('home.html', fbid=fb_id,
            classes=find_registered_classes(fb_id), friends=baguette_friends,
            first_name=first_name)
#    return '%s user (fb_id: %s) with access_token %s' % (created, fb_id, access_token)
#    return content

@app.route('/about')
def about():
    fbid = "nope"
    dbg = 'eee'
    if 'fb_id' in session:
        fbid = session['fb_id']
    return render_template('about.html', fbid=fbid)

@app.route('/calendar')
def calendar():
    return render_template('calendar.html')

def getClassesForFBID(fbid):
    return db.classes.Class.find({'userlist': unicode(fbid)})

def timeToFloat(timeStr):
    """8:30 or 3"""
    if '.' in timeStr:
        time = float(timeStr.split('.')[0]) + 0.5
    else:
        time = float(timeStr)
    if time < 8:
        time += 12
    return time

def makeClassSchedule(cl, color=0):
    schedule = []
    time = getTimeForClass(cl)
    try:
        days = re.match('([MTWRF]+)', time).group(1)
    except Exception:
        return []
    if '-' in time:
        print time
        first  = re.match('[MTWRF]*([0-9.]+)-([0-9.]+)', time).group(1)
        second = re.match('[MTWRF]*([0-9.]+)-([0-9.]+)', time).group(2)
        ttime = timeToFloat(first)
        endtime = timeToFloat(second)
        length = endtime - ttime
    else:
        try:
            first = re.match('[MTWRF]*([0-9]+)', time).group(1)
        except Exception:
            return []
        ttime = timeToFloat(first)
        length = 1.0
    for c in days:
        s = {
                'name': cl['name'],
                'day': c,
                'time': ttime,
                'length': length,
                'color': color,
                'type': 'LEC',
            }
        schedule.append(s)
    return schedule

def makeMyClassSchedule(cl, fbid, color=0):
    schedule = []
    time = getTimeForClass(cl)
    if fbid not in cl['usersessions']:
        return schedule
    for session in cl['usersessions'][fbid]:
        time = getTimeForSessionClass(session, cl)
        print session, time
        if time is None:
            continue
        try:
            days = re.match('([MTWRF]+)', time).group(1)
        except Exception:
            continue
        if '-' in time:
            print time
            first  = re.match('[MTWRF]*([0-9.]+)-([0-9.]+)', time).group(1)
            second = re.match('[MTWRF]*([0-9.]+)-([0-9.]+)', time).group(2)
            ttime = timeToFloat(first)
            endtime = timeToFloat(second)
            length = endtime - ttime
        else:
            try:
                first = re.match('[MTWRF]*([0-9]+)', time).group(1)
            except Exception:
                continue
            ttime = timeToFloat(first)
            length = 1.0
        ts = session[0]
        if ts == 'L':
            stype = 'LEC'
        elif ts == 'R':
            stype = 'REC'
        else:
            stype = 'LAB'
        for c in days:
            s = {
                    'name': cl['name'],
                    'day': c,
                    'time': ttime,
                    'length': length,
                    'color': color,
                    'type': stype,
                }
            schedule.append(s)
    return schedule

@app.route('/user/<userid>')
def show_user(userid):
    fbid = ''
    if 'fb_id' in session:
        fbid = session['fb_id']
    else:
        if not BYPASS:
            raise AuthError
    if BYPASS:
        friendList = []
    else:
        friendList = get_friends()
    #for f in friendList:
    #    if unicode(f['uid']) in classTakers:
    #        friendClassTakers.append(f)
    user_profile = getUserProfile(userid)
    classesCursor = getClassesForFBID(userid)
    classes = []
    for cl in classesCursor:
        classes.append(cl)
    schedule = []
    colorcounter = 0
    for cl in classes:
        schedule += makeMyClassSchedule(cl, userid, color=colorcounter)
        print schedule
        colorcounter += 1
    return render_template('user.html', classes=classes, fbid=fbid,
            schedule=schedule, user_profile=user_profile)

def getTimeForSessionClass(sessionName, cl):
    for s in cl['sessions']:
        if s['label'] == sessionName:
            return s['time']

def getTimeForClass(cl):
    for s in cl['sessions']:
        if s['type'] == u'lecture':
            return s['time']


@app.route('/fixclasses')
def fixClasses():
    for cl in db.classes.Class.find():
        cl['usersessions'] = {}
        cl.save()
        userlist = cl['userlist']
        for u in userlist:
            print cl['name']
            print u
            untakeClass(cl, u)
            takeClass(cl, u)
    return ""

if __name__ == '__main__':
    app.debug = True
    port = int(os.environ.get('PORT', 5005))
    app.run(host='0.0.0.0', port=port)
