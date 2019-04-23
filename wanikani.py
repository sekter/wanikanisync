# wanikani2anki, import unlocked Kanji and Vocab from WaniKani to a
# deck in desktop Anki 2.0.x.  place this file in your desktop Anki 2
# addons folder.

# from https://github.com/nigelkerr/wanikani2anki and in the public
# domain, with no sort of warranty whatsoever.

from aqt import mw
from aqt.utils import showInfo, showCritical, askUser
from aqt.qt import *
from anki.importing.noteimp  import NoteImporter, ForeignNote

import re
from urllib.request import urlopen, Request
import json

# HTTPS cert validation failure workaround (man in the middle attac is possible!!!)
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

WK_KANJI_URL = 'https://api.wanikani.com/v2/subjects?hidden=false&types=kanji'
WK_VOCAB_URL = 'https://api.wanikani.com/v2/subjects?hidden=false&types=vocabulary'
WK_ASSIGNMENT_URL = 'https://api.wanikani.com/v2/assignments?unlocked=true&subject_types={}'
WK_USER_URL  = 'https://api.wanikani.com/v2/user'

WKH_REV_KEY   = 'Wanikani-Revision'
WKH_AUTH_KEY = 'Authorization'
WKH_AUTH_VALUE = 'Bearer {}'
WKH_LEVELS_KEY = 'levels'

WK_CSS = """.card {font-family: sans forgetica, arial; font-size: 20px; text-align: center; color: black; background-color: white;}
.background-div{position: fixed; top: 0px; bottom: 0px; left: 0px; right: 0px; z-index: -1;}
.kunyomi {background-color: Pink;}
.onyomi  {background-color: PaleGoldenRod;}
.norm {font-family: arial;}
.jp { font-size: 50px }
.pofspeech {font-style: italic; font-size: 15px;color:brown}
.recog { background-color:lightgrey; font-style: italic; font-weight:bold; font-size: 15px; color:black; text-align:left}
.read { background-color:black; font-style: italic; font-weight:bold; font-size: 15px; color:white; text-align:left}
.recallw { background-color:lightgrey; font-style: italic; font-weight:bold; font-size: 15px; color:blue; text-align:left}
.recallr {background-color:blue; font-style: italic;  font-weight:bold; font-size: 15px; color:white; text-align:left}
.win .jp { font-family: "MS Mincho", "ＭＳ 明朝"; }
.mac .jp { font-family: "Hiragino Mincho Pro", "ヒラギノ明朝 Pro"; }
.linux .jp { font-family: "Kochi Mincho", "東風明朝"; }
.mobile .jp { font-family: "Hiragino Mincho ProN"; }"""

WK_CONF = mw.addonManager.getConfig(__name__)

class WaniKaniImporter(NoteImporter):
    def __init__(self, *args):
        NoteImporter.__init__(self, *args)
        self.allowHTML = True
        self.availableIds = set();
        
    def foreignNotes(self):
        notes = []
        for item in self.correctPart():
            note = self.noteFromJson(item)
            if note:
                notes.append(note)
        return notes

    def correctPart(self):
        return self.file[u'data']

    def noteFromJson(self,jsonDict):
        return None

class WKKanjiImporter(WaniKaniImporter):
    def __init(self, *args):
        WaniKaniImporter.__init(self, *args)

    def fields(self):
        return 10 # number of field (from the beginning) we import

    def noteFromJson(self,jsonDict):
        note = None
        if (jsonDict[u'object'] == 'kanji' and jsonDict[u'id'] in self.availableIds):
            note = ForeignNote()
            
            # appending as a number anki throws an Exception
            note.fields.append('{}'.format(jsonDict[u'id']))
            
            # appending as a number anki throws an Exception
            note.fields.append('{}'.format(jsonDict[u'data'][u'level']))
            
            # appending as a number anki throws an Exception
            note.fields.append('{}'.format(jsonDict[u'data'][u'lesson_position']))
            
            note.fields.append(jsonDict[u'data'][u'characters'])

            note.fields.append(joinValues(jsonDict[u'data'][u'meanings'], u'meaning')[1])
            
            note.fields.append(jsonDict[u'data'][u'meaning_mnemonic'])
            
            opcount, onyomi = joinValues(jsonDict[u'data'][u'readings'], u'reading', u'onyomi')
            kpcount, kunyomi = joinValues(jsonDict[u'data'][u'readings'], u'reading', u'kunyomi')
            
            note.fields.append(onyomi)
            
            # if kanji has primary onyomi and kunyomi reading too, then reading mnemonic
            # is put both in onyomi and kunyomi reading mnemonic
            if (opcount > 0 and kpcount == 0) or (kpcount > 0 and opcount > 0):
                note.fields.append(jsonDict[u'data'][u'reading_mnemonic'])
            else:
                note.fields.append(u'')
            
            note.fields.append(kunyomi)

            # if kanji has primary onyomi and kunyomi reading too, then reading mnemonic
            # is put both in onyomi and kunyomi reading mnemonic
            if (kpcount > 0 and opcount == 0) or (kpcount > 0 and opcount > 0):
                note.fields.append(jsonDict[u'data'][u'reading_mnemonic'])
            else:
                note.fields.append(u'')

        return note


class WKVocabImporter(WaniKaniImporter):
    def __init(self, *args):
        WaniKaniImporter.__init(self, *args)
        
    def fields(self):
        return 9 # number of field (from the beginning) we import

    def noteFromJson(self,jsonDict):
        note = None
        if (jsonDict[u'object'] == 'vocabulary' and jsonDict[u'id'] in self.availableIds):
            note = ForeignNote()
            
            # appending as a number anki throws an Exception
            note.fields.append('{}'.format(jsonDict[u'id']))
            
            # appending as a number anki throws an Exception
            note.fields.append('{}'.format(jsonDict[u'data'][u'level']))
            
            # appending as a number anki throws an Exception
            note.fields.append('{}'.format(jsonDict[u'data'][u'lesson_position']))
            
            note.fields.append(jsonDict[u'data'][u'characters'])

            note.fields.append(joinValues(jsonDict[u'data'][u'meanings'], u'meaning')[1])
            
            note.fields.append(jsonDict[u'data'][u'meaning_mnemonic'])
            
            note.fields.append(joinValues(jsonDict[u'data'][u'readings'], u'reading')[1])
            
            note.fields.append(jsonDict[u'data'][u'reading_mnemonic'])

            note.fields.append(", ".join(jsonDict[u'data'][u'parts_of_speech']))
            
        return note

# the highest available WaniCani level
def getWKMaxLevel():
    req = Request(WK_USER_URL)
    req.add_header(WKH_REV_KEY, WK_CONF['WK Revision'])
    req.add_header(WKH_AUTH_KEY, WKH_AUTH_VALUE.format(WK_CONF['WK API Key']))
    user = getJsonResponseFromWK(req)
    return min(user['data']['level'],user['data']['subscription']['max_level_granted'])

# get the set of unlocked subject IDs
def getWKAvailableSubjectIds(type):
    url = WK_ASSIGNMENT_URL.format(type)
    retVal = set()
    while url:
        assignments = callWaniKani(url)
        if not assignments:
            showCritical("No response from WaniKani, the deck is partially filled.")
            break

        retVal = retVal | set(x[u'data'][u'subject_id'] for x in assignments[u'data'] if x[u'data'][u'srs_stage']>0)
        url = assignments[u'pages'][u'next_url']

    return retVal

# proceessing json list structures to return the values in a single text
# concatenating the jsonField values from the list items
# type: items with this type are selected or all selected if type==None
# if an item is a primary item then its value enclosed between <b> and </b> 
# returns a string containing a comma separated list
def joinValues(inputJson, jsonField, type=None):
    content =""
    sep=""
    primaryCount = 0
    for item in inputJson:
        if not type or (type and item[u'type'] == type):
            if item[u'primary']:
                content = '<b>' + item[jsonField] + '</b>' + ("" if not sep else sep + " ") + content
                primaryCount = primaryCount + 1
            else:
                content = content + ("" if not sep else sep + " ") + item[jsonField]
            if not sep:
                sep ="&comma;"
    return (primaryCount, content)

def getJsonResponseFromWK(req):
    parsed = None
    try:
        response = urlopen(req)
        data = response.read()
        parsed = json.loads(data)
    except Exception as e:
        showInfo('Connection to WaniKani is failed: {}'.format(e))
    return parsed

# calls the given WK url and returns a response in json format
def callWaniKani(url):
    req = Request(url)
    req.add_header(WKH_REV_KEY, WK_CONF['WK Revision'])
    req.add_header(WKH_AUTH_KEY, WKH_AUTH_VALUE.format(WK_CONF['WK API Key']))
    return getJsonResponseFromWK(req)

def updateWKKanjiDeck():
    
    # select deck
    deckId = mw.col.decks.id(WK_CONF['WK Kanji Deck Name'])
    mw.col.decks.select(deckId)
    # anki defaults to the last note type used in the selected deck
    model = mw.col.models.byName(WK_CONF['WK Kanji Model Name'])
    deck = mw.col.decks.get(deckId)
    deck['mid'] = model['id']
    mw.col.decks.save(deck)
    # set the last deck used by this note type -» puts this note in the last used deck
    model['did'] = deckId
    mw.col.models.save(model)

    NumONotes = len(mw.col.findNotes("'note:{}'".format(WK_CONF['WK Kanji Model Name'])))

    # let import the notes page by page
    # just the available levels
    # be careful the WK_KANJI_URL contains the type parameter so the levels is added to by &
    availableKanjiIds = getWKAvailableSubjectIds("kanji")
    url = WK_KANJI_URL+"&"+WKH_LEVELS_KEY+"="+",".join(str(x) for x in list(range(1, getWKMaxLevel()+1)))
    while url:
        kanjiJson = callWaniKani(url)
        if not kanjiJson:
            showCritical("No response from WaniKani, the deck is partially filled.")
            break
        wki = WKKanjiImporter(mw.col,kanjiJson)
        # ignore if first field matches existing note (0 update - default, 2 import)
        wki.importMode = 1
        wki.availableIds = availableKanjiIds;
        wki.initMapping()
        wki.run()
        url = kanjiJson[u'pages'][u'next_url']
        
    mw.app.processEvents()
    mw.deckBrowser.show()
    showInfo("WaniKani Kanji Syncroniser added {} new kanji(s) to Anki.".format(len(mw.col.findNotes("'note:{}'".format(WK_CONF['WK Kanji Model Name']))) - NumONotes))

def createWKKanjiModel():
    wkKanjiModel = mw.col.models.new(WK_CONF['WK Kanji Model Name'])
    mw.col.models.addField(wkKanjiModel, mw.col.models.newField("Id"))
    mw.col.models.addField(wkKanjiModel, mw.col.models.newField("Level"))
    mw.col.models.addField(wkKanjiModel, mw.col.models.newField("Lesson position"))
    mw.col.models.addField(wkKanjiModel, mw.col.models.newField("Kanji"))
    mw.col.models.addField(wkKanjiModel, mw.col.models.newField("Meaning"))
    mw.col.models.addField(wkKanjiModel, mw.col.models.newField("Meaning mnemonic"))
    mw.col.models.addField(wkKanjiModel, mw.col.models.newField("On'yomi"))
    mw.col.models.addField(wkKanjiModel, mw.col.models.newField("On'yomi mnemonic"))
    mw.col.models.addField(wkKanjiModel, mw.col.models.newField("Kun'yomi"))
    mw.col.models.addField(wkKanjiModel, mw.col.models.newField("Kun'yomi mnemonic"))
    mw.col.models.addField(wkKanjiModel, mw.col.models.newField("Diagram"))
    if WK_CONF['Kanji recognition card']:
        tmpl = mw.col.models.newTemplate("Recognition")
        tmpl['qfmt'] = "<div class='recog norm'>Meaning</div><br><div class=jp> {{Kanji}} </div>"
        tmpl['afmt'] = "{{FrontSide}}<hr id=answer>{{Meaning}}"
        mw.col.models.addTemplate(wkKanjiModel, tmpl)
    if WK_CONF["On'yomi reading card"]:
        tmpl = mw.col.models.newTemplate("On'yomi")
        tmpl['qfmt'] = "<div class='norm read'>on'yomi</div><br>{{#On'yomi}}<div class='background-div onyomi'></div><div class=jp> {{Kanji}} </div><br>{{/On'yomi}}"
        tmpl['afmt'] = "{{FrontSide}}<hr id=answer><div class='background-div onyomi'></div>{{On'yomi}}<br><div class=norm>{{On'yomi mnemonic}}</div>"
        mw.col.models.addTemplate(wkKanjiModel, tmpl)
    if WK_CONF["Kun'yomi reading card"]:
        tmpl = mw.col.models.newTemplate("Kun'yomi")
        tmpl['qfmt'] = "<div class='norm read'>kun'yomi</div><br>{{#Kun'yomi}}<div class='background-div kunyomi'></div><div class=jp> {{Kanji}} </div><br>{{/Kun'yomi}}"
        tmpl['afmt'] = "{{FrontSide}}<hr id=answer><div class='background-div kunyomi'></div>{{Kun'yomi}}<br><div class=norm>{{Kun'yomi mnemonic}}</div>"
        mw.col.models.addTemplate(wkKanjiModel, tmpl)
    if WK_CONF["Stroke order card"]:
        tmpl = mw.col.models.newTemplate("Stroke order")
        tmpl['qfmt'] = "{{#Diagram}}<div class='recallw norm'>Stroke order</div><div class=jp> {{Kanji}} </div><br><br>{{/Diagram}}"
        tmpl['afmt'] = "{{Diagram}}{{^Diagram}}<div class=norm>Please download the 'Kanji Colorizer stroke order diagram' add-on and generate all diagrams!</div>{{/Diagram}}"
        mw.col.models.addTemplate(wkKanjiModel, tmpl)

    wkKanjiModel['css'] = WK_CSS

    mw.col.models.add(wkKanjiModel)
    # set this model on the related deck
    deckId = mw.col.decks.id(WK_CONF['WK Kanji Deck Name'])
    deck = mw.col.decks.get(deckId)
    deck['mid'] = wkKanjiModel['id']
    mw.col.decks.save(deck)

    # set the last deck used by this note type -» puts this note in the last used deck
    wkKanjiModel['did'] = deckId
    mw.col.models.save(wkKanjiModel)


    mw.app.processEvents()
    mw.deckBrowser.show()

def updateWKVocabDeck():
    
    # select deck
    deckId = mw.col.decks.id(WK_CONF['WK Vocab Deck Name'])
    mw.col.decks.select(deckId)
    # anki defaults to the last note type used in the selected deck
    model = mw.col.models.byName(WK_CONF['WK Vocab Model Name'])
    deck = mw.col.decks.get(deckId)
    deck['mid'] = model['id']
    mw.col.decks.save(deck)
    # set the last deck used by this note type -» puts this note in the last used deck
    model['did'] = deckId
    mw.col.models.save(model)

    NumONotes = len(mw.col.findNotes("'note:{}'".format(WK_CONF['WK Vocab Model Name'])))

    # let import the notes page by page
    # just the available levels
    # be careful the WK_KANJI_URL contains the type parameter so the levels is added to by &
    availableVocabIds = getWKAvailableSubjectIds("vocabulary")
    url = WK_VOCAB_URL+"&"+WKH_LEVELS_KEY+"="+",".join(str(x) for x in list(range(1, getWKMaxLevel()+1)))
    while url:
        vocabJson = callWaniKani(url)
        if not vocabJson:
            showCritical("No response from WaniKani, the deck is partially filled.")
            break
        wki = WKVocabImporter(mw.col,vocabJson)
        # ignore if first field matches existing note (0 update - default, 2 import)
        wki.importMode = 1
        wki.availableIds = availableVocabIds;
        wki.initMapping()
        wki.run()
        url = vocabJson[u'pages'][u'next_url']
        
    mw.app.processEvents()
    mw.deckBrowser.show()
    showInfo("WaniKani Vocab Syncroniser added {} new word(s) to Anki.".format(len(mw.col.findNotes("'note:{}'".format(WK_CONF['WK Vocab Model Name']))) - NumONotes))


def createWKVocabModel():
    wkVocabModel = mw.col.models.new(WK_CONF['WK Vocab Model Name'])
    mw.col.models.addField(wkVocabModel, mw.col.models.newField("Id"))
    mw.col.models.addField(wkVocabModel, mw.col.models.newField("Level"))
    mw.col.models.addField(wkVocabModel, mw.col.models.newField("Lesson position"))
    mw.col.models.addField(wkVocabModel, mw.col.models.newField("Expression"))
    mw.col.models.addField(wkVocabModel, mw.col.models.newField("Meaning"))
    mw.col.models.addField(wkVocabModel, mw.col.models.newField("Meaning mnemonic"))
    mw.col.models.addField(wkVocabModel, mw.col.models.newField("Reading"))
    mw.col.models.addField(wkVocabModel, mw.col.models.newField("Reading mnemonic"))
    mw.col.models.addField(wkVocabModel, mw.col.models.newField("Parts of speech"))
    if WK_CONF['Vocab recognition card']:
        tmpl = mw.col.models.newTemplate("Recognition")
        tmpl['qfmt'] = "<div class='norm recog'>Meaning</div><br><div class=jp> {{Expression}} </div>"
        tmpl['afmt'] = "{{FrontSide}}<hr id=answer>{{Meaning}}<br><div class=norm><div class=pofspeech>{{Parts of speech}}</div><br>{{Meaning mnemonic}}</br>"
        mw.col.models.addTemplate(wkVocabModel, tmpl)
    if WK_CONF["Reading card"]:
        tmpl = mw.col.models.newTemplate("Reading")
        tmpl['qfmt'] = "<div class='norm read'>Reading</div><br><div class=jp> {{Expression}}</div>"
        tmpl['afmt'] = "{{FrontSide}}<hr id=answer>{{Reading}}<br><div class=norm>{{Reading mnemonic}}</div>"
        mw.col.models.addTemplate(wkVocabModel, tmpl)
    if WK_CONF["Recall reading card"]:
        tmpl = mw.col.models.newTemplate("Recall reading")
        tmpl['qfmt'] = "<div class=norm><div class=recallr>Reading</div><br>{{Meaning}}<br><div class=pofspeech>{{Parts of speech}}</div>"
        tmpl['afmt'] = "{{FrontSide}}<hr id=answer>{{Reading}}<br>{{Reading mnemonic}}"
        mw.col.models.addTemplate(wkVocabModel, tmpl)
    if WK_CONF["Recall writing card"]:
        tmpl = mw.col.models.newTemplate("Recall writing")
        tmpl['qfmt'] = "<div class=norm><div class=recallw>Writing</div><br>{{Meaning}}<br><div class=pofspeech>{{Parts of speech}}</div></div>"
        tmpl['afmt'] = "{{FrontSide}}<hr id=answer><div class=jp> {{Expression}} </div>"
        mw.col.models.addTemplate(wkVocabModel, tmpl)

    wkVocabModel['css'] = WK_CSS

    mw.col.models.add(wkVocabModel)
    # set this model on the related deck
    deckId = mw.col.decks.id(WK_CONF['WK Vocab Deck Name'])
    deck = mw.col.decks.get(deckId)
    deck['mid'] = wkVocabModel['id']
    mw.col.decks.save(deck)

    # set the last deck used by this note type -» puts this note in the last used deck
    wkVocabModel['did'] = deckId
    mw.col.models.save(wkVocabModel)

    mw.app.processEvents()
    mw.deckBrowser.show()

def doWaniKaniSync():
    if WK_CONF['WK Kanji Syncronization']:
        if not mw.col.models.byName(WK_CONF['WK Kanji Model Name']):
            createWKKanjiModel()
        updateWKKanjiDeck()
    
    if WK_CONF['WK Vocab Syncronization']:
        if not mw.col.models.byName(WK_CONF['WK Vocab Model Name']):
            createWKVocabModel()
        updateWKVocabDeck()
#------------------------------------------------------

# add menu item
WKAction = QAction("WaniKani Syncroniser", mw)
WKAction.triggered.connect(doWaniKaniSync)
mw.form.menuTools.addAction(WKAction)

