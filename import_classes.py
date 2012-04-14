import json
from database import db

#db.drop_collection('classes')

classes = json.load(open('res/courses.json'))["items"]

for cl in classes:
    if 'id' not in cl.keys():
        continue
    type = cl['type']
    name = cl['id']
    label = cl['label']
    description = cl['description']
    professor = cl['in-charge']
    if professor == None:
        professor = ''
            
    dbcl = db.classes.Class.find_one({'name': name}) or db.classes.Class()
    dbcl['name'] = name
    dbcl['label'] = label
    dbcl['description'] = description
    dbcl['professor'] = professor
    dbcl.save()
       
    '''    
    if type == 'Class':
        name = cl['id']
        label = cl['label']
        description = cl['description']
        professor = cl['in-charge']
        if professor == None:
            professor = ''
            
        dbcl = db.classes.Class()
        dbcl['name'] = name
        dbcl['label'] = label
        dbcl['description'] = description
        dbcl['professor'] = professor
        dbcl.save()

    elif type == 'LectureSession':
        parent = cl['section-of']
        timePlace = cl['timeAndPlace'].split(" ")
        if len(timePlace) == 4:
            time = timePlace[0,2]
            place = timePlace[3]
        if timePlace[0] == "*TO":
            time = "TBD"
            place = "TBD"
        else:
            time = timePlace[0]
            place = timePlace[1]
        cl = db.classes.find_one({'name': parent})
        cl['lecture'].append([time, place])
        cl.save()
        
    elif type == 'RecitationSession':
        parent = cl['section-of']
        timePlace = cl['timeAndPlace'].split(" ")
        time = timePlace[0]
        place = timePlace[1]
        cl = db.classes.find_one({'name': parent})
        cl['recitation'].append([time, place])
        cl.save()
    '''
