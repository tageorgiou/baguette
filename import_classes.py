import json
from database import db

db.drop_collection('classes')

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
            
    dbcl = db.classes.Class()
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
        timePlace = cl['timeAndPlace']
        cl = db.classes.find_one({'name': parent})
        cl['lecture'].append(timePlace)
        cl.save()
        
    elif type == 'RecitationSession':
        parent = cl['section-of']
        timePlace = cl['timeAndPlace']
        cl = db.classes.find_one({'name': parent})
        cl['recitation'].append(timePlace)
        cl.save()
    '''
        
