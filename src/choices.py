from flask import Flask, request, make_response, jsonify
from datetime import datetime
import time
import symspellpy
from symspellpy.verbosity import Verbosity

app = Flask(__name__)

def convertName(name):
    return name[0].upper() if len(name) <= 1 else name[0].upper() + name[1:].lower()

def createSuggestions(suggObject, name):
    newSuggestions = []
    whoExists = [False, False]
    for sug in suggObject:
        data = {"name": sug.term, "closeness": sug.distance, "count": sug.count}
        if sug.distance in [0, 1] and not whoExists[sug.distance]:
            whoExists[sug.distance] = True
        else: #elif sug.distance == 2:
            if len(newSuggestions) >= 15 and (whoExists[0] or whoExists[1]):
                continue
        if sug.term.lower() == name:
            newSuggestions.insert(0, data)
        else:
            newSuggestions.append(data)
    return newSuggestions

def createResponse(data, status: int=200):
    res = make_response(jsonify(({"status": status, "message": data})))
    res.headers['Access-Control-Allow-Origin'] = '*'
    return res

def createError(error, status):
    return createResponse(str(error), status)

def queryError(name, nameType):
    msg = ""
    if name is None or name == "":
        msg += messages["EMPTY_NAME"]
    elif nameType is None or nameType == "":
        msg += messages["EMPTY_TYPE"]
    elif nameType.lower() not in ("first", "last", "both"):
        msg += messages["BAD_TYPE"]
    return None if not msg else msg + " try /search?name=john&type=brown"


@app.errorhandler(404)
def invalidRoute(e):
    return createError(messages["BAD_ROUTE"], 404)


@app.route('/time', methods=['GET'])
def getTime():
    try:
        return createResponse("Took " + str(end -  start) + " seconds")
    except Exception as e:
        return createError(str(e), 500)


@app.route('/search', methods=['GET', 'POST'])
def search():
    try:
        if request.method == 'GET':
            name = request.args.get('name')
            nameType = request.args.get('type')
        if request.method == 'POST':
            name = request.form['name']
            nameType = request.form['type']
        error = queryError(name, nameType)
        if error:
            return createError(error, 400)
        else:
            name = convertName(name)
            nameType = nameType.lower()
            if nameType == "first": # or nameType not in ["last", "both"]
                suggestions = createSuggestions(sym_spell_first.lookup(name, verbosity=Verbosity.ALL), name)
            elif nameType == "last":
                suggestions = createSuggestions(sym_spell_last.lookup(name, verbosity=Verbosity.ALL), name)
            elif nameType == "both":
                suggestions = {"first": createSuggestions(sym_spell_first.lookup(name, verbosity=Verbosity.CLOSEST), name),
                "last": createSuggestions(sym_spell_last.lookup(name, verbosity=Verbosity.CLOSEST), name)}
            return createResponse(suggestions)
    except Exception as e:
        return createError(str(e), 500)

messages = {
    "BAD_ROUTE": "Invalid Route, use /search",
    "EMPTY_NAME": "Invalid Query, name is empty",
    "EMPTY_TYPE": "Invalid Query, type is empty",
    "BAD_TYPE": "Invalid Query, unsupported type: must be first, last, both"
}

sym_spell_first = symspellpy.SymSpell()
sym_spell_last = symspellpy.SymSpell()

sym_spell_first.load_dictionary("site/data/firsts.csv", term_index=0, count_index=1, separator=",", encoding="utf8")
sym_spell_last.load_dictionary("site/data/lasts.csv", term_index=0, count_index=1, separator=",", encoding="utf8")