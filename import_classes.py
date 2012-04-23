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
        if professor == 'null':
            prof = ['']
        else: 
            prof = professor.split(',')
            if prof[1] == '':
                prof = [prof[0]]
            else: prof = [prof[1][1] + '. ' + prof[0]]
        springProf = cl['spring_instructors']
        for p in springProf:
            mult = p.split(':')
            if len(mult) != 1:
                if len(mult) == 7:
                    prof.append('R. B. Melrose')
                    prof.append('H.R. Miller')
                    p = ''
                else: p = mult[1][1:]
            if p != prof[0] and p != '': prof.append(p)
            
        dbcl['name'] = name
        dbcl['label'] = label
        dbcl['description'] = description
        dbcl['professor'] = prof
        dbcl.save()

#second pass for sessions
for cl in classes:
    cltype = cl['type']
    print cl['label']
    if cltype == 'LectureSession':
        parent = cl['section-of']
        timePlace = cl['timeAndPlace'].split()
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
        
    elif cltype == 'RecitationSession':
        parent = cl['section-of']
        timePlace = cl['timeAndPlace'].split()
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
        print 'class, continue'
        continue
    else:
        print cltype
