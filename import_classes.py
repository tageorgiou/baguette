import json
from database import db

db.drop_collection('classes')

classes = json.load(open('res/courses.json'))["items"]

#first pass for classes
for cl in classes:
    cltype = cl['type']
    if cltype == 'Class':
        name = cl['id']
        dbcl = db.classes.Class.find_one({'name': unicode(name)}) or \
            db.classes.Class()
        label = cl['label']
        description = cl['description']
        professor = cl['in-charge']
        if professor == None:
            professor = ''
            
        dbcl['name'] = name
        dbcl['label'] = label
        dbcl['description'] = description
        dbcl['professor'] = professor
        dbcl.save()

#second pass for sessions
for cl in classes:
    print label
    if cltype == 'LectureSession':
        parent = cl['section-of']
        timePlace = cl['timeAndPlace'].split(" ")
        label = cl['label']
        if len(timePlace) == 4:
            time = timePlace[0:2]
            place = timePlace[3]
        if timePlace[0] == "*TO":
            time = "TBD"
            place = "TBD"
        else:
            time = timePlace[0]
            place = timePlace[1]
        dbcl = db.classes.Class.find_one({'name': unicode(parent)})
        if dbcl is None:
            print "ERR", label
            continue
        sess = {
                'type': 'lecture',
                'time': time,
                'place': place,
                'label': label,
                }
        dbcl['sessions'].append(sess)
        dbcl.save()
        
    elif type == 'RecitationSession':
        parent = cl['section-of']
        timePlace = cl['timeAndPlace'].split(" ")
        time = timePlace[0]
        place = timePlace[1]
        dbcl = db.classes.Class.find_one({'name': unicode(parent)})
        if dbcl is None:
            print "ERR", label
            continue
        sess = {
                'type': 'recitation',
                'time': time,
                'place': place,
                'label': label,
                }
        dbcl['sessions'].append(sess)
        dbcl.save()
    elif cltype == 'Class':
        continue
    else:
        print cltype
