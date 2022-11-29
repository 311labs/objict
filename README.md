![](https://github.com/311labs/objict/workflows/tests/badge.svg)

## Turn a dict into an Object or objict!

Based on uberdict(https://raw.githubusercontent.com/eukaryote/uberdict)

## Installation

```
pip install pyobjict
```


### Some Differences:

 * Support for to/from JSON
 * Support for to/from XML
 * Support for to/from ZIP compression (base64)
 * Support to/from file
 * When an attribute is not found it returns None instead of raising an Error
 * Support for .get("a.b.c")
 * Support for delta between to objicts (obj.changes())
 * Will automatically handle key conversion from "a.b.c" to "a -> b -> c" creation


## Simple to use!

```python
>>> from objict import objict
>>> d1 = objict(name="John", age=24)
>>> d1
{'name': 'John', 'age': 24}
>>> d1.name
'John'
>>> d1.age
24
>>> d1.gender = "male"
>>> d1
{'name': 'John', 'age': 24, 'gender': 'male'}
>>> d1.gender
'male'
>>> import datetime
>>> d1.dob = datetime.datetime(1985, 5, 2)
>>> d1.dob
datetime.datetime(1985, 5, 2, 0, 0)
>>> d1.toJSON()
{'name': 'John', 'age': 24, 'gender': 'male', 'dob': 483865200.0}
>>> d1.save("test1.json")
>>> d2 = objict.fromFile("test1.json")
>>> d2
{'name': 'John', 'age': 24, 'gender': 'male', 'dob': 483865200.0}
>>> d2.toXML()
'<name>John</name><age>24</age><gender>male</gender><dob>483865200.0</dob>'
>>> d3 = objict(user1=d2)
>>> d3.user2 = objict(name="Jenny", age=27)
>>> d3
{'user1': {'name': 'John', 'age': 24, 'gender': 'male', 'dob': 483865200.0}, 'user2': {'name': 'Jenny', 'age': 27}}
>>> d3.toXML()
'<user1><name>John</name><age>24</age><gender>male</gender><dob>483865200.0</dob></user1><user2><name>Jenny</name><age>27</age></user2>'
>>> d3.toJSON(True)
'{\n    "user1": {\n        "name": "John",\n        "age": 24,\n        "gender": "male",\n        "dob": 483865200.0\n    },\n    "user2": {\n        "name": "Jenny",\n        "age": 27\n    }\n}'
>>> print(d3.toJSON(True))
{
    "user1": {
        "name": "John",
        "age": 24,
        "gender": "male",
        "dob": 483865200.0
    },
    "user2": {
        "name": "Jenny",
        "age": 27
    }
}
>>> d3.toZIP()
b'x\x9c\xab\xe6R\x00\x02\xa5\xd2\xe2\xd4"C%+\x85j0\x17,\x94\x97\x98\x9b\n\x14Q\xf2\xca\xcf\xc8S\xd2A\x88\'\xa6\x83\x84\x8dL\x90\x84\xd2S\xf3RR\x8b@\x8as\x13sR\x91\x15\xa7\xe4\'\x01\x85M,\x8c-\xccL\x8d\x0c\x0c\xf4\x0c\xc0R\xb5:\x08[\x8dp\xd8\x9a\x9a\x97W\x89\xc5Zs\x88\x01\\\xb5\x00^\x1c\'I'
>>> dz = d3.toZIP()
>>> d4 = objict.fromZIP(dz)
>>> d4
{'user1': {'name': 'John', 'age': 24, 'gender': 'male', 'dob': 483865200.0}, 'user2': {'name': 'Jenny', 'age': 27}}
>>> d5 = d4.copy()
>>> d5.user1.name
'John'
>>> d5.user1.name = "Jim"
>>> d5
{'user1': {'name': 'Jim', 'age': 24, 'gender': 'male', 'dob': 483865200.0}, 'user2': {'name': 'Jenny', 'age': 27}}
>>> d5.changes(d4)
{'user1': {'name': 'John'}}

```


