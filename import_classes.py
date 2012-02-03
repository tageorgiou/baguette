import json
from database import db

classes = json.load(open('res/courses.json'))["items"]

for cl in classes:
    if 'id' not in cl.keys():
        continue
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
