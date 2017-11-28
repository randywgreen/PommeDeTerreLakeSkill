import urllib2
import json
from HTMLParser import HTMLParser
from itertools import tee, islice, chain, izip

LAKE_URL = "http://www.nwk.usace.army.mil/Locations/District-Lakes/Pomme-de-Terre-Lake/Daily-Lake-Info-2/"

class MyHTMLParser(HTMLParser):

    def __init__(self):
        HTMLParser.__init__(self)
        self.recording = 0
        self.data = []


    def handle_starttag(self, tag, attributes):
        if tag != 'div':
            return
        if self.recording:
            self.recording += 1
            return
        for name, value in attributes:
            #div id that contains our data
            if name == 'id' and value == 'dnn_ctr82367_HtmlModule_lblContent':
                break
            else:
                return
        self.recording = 1


    def handle_endtag(self, tag):
        if tag == 'div' and self.recording:
            self.recording -= 1


    def handle_data(self, data):
        if self.recording:
            self.data.append(data)


# --------------- Helpers that build all of the responses ----------------------

def build_speechlet_response(title, output, content, reprompt_text, should_end_session):
    if content: 
        return {
            'outputSpeech': {
                'type': 'PlainText',
                'text': output
            },
            'card': {
                'type': 'Simple',
                'title': title,
                'content': content
            },
            'reprompt': {
                'outputSpeech': {
                    'type': 'PlainText',
                    'text': reprompt_text
                }
            },
            'shouldEndSession': should_end_session
        }
    else :
        return {
            'outputSpeech': {
                'type': 'PlainText',
                'text': output
            },
            'reprompt': {
                'outputSpeech': {
                    'type': 'PlainText',
                    'text': reprompt_text
                }
            },
            'shouldEndSession': should_end_session
        }


def build_response(session_attributes, speechlet_response):
    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }


# --------------- Functions that control the skill's behavior ------------------

def get_daily_info(session):
    session_attributes = {}
    speech_output = ""
    if 'attributes' in session :
        session_attributes = session['attributes']
    card_title = "Daily Information"
    reprompt_text = "Please tell me what other information you would like by saying, " \
                    "tell me about the lake, tell me the history, or cancel."
    should_end_session = False
    
    if session.get('attributes', {}) :
        if "normalElevation" in session.get('attributes', {}) :
            #print "***normalElevation in session***"
            normal_elevation = session['attributes']['normalElevation']
        
        if "currElevation" in session.get('attributes', {}) :
            #print "***currElevation in session***"
            curr_elevation = session['attributes']['currElevation']
            speech_output += "The lakes current elavation is " + str(int(float(curr_elevation))) + " feet. "
            
        if "lakeLevel" in session.get('attributes', {}) :
            #print "***lakeLevel in session***"
            level = session['attributes']['lakeLevel']
            speech_output += "This is" + level + "than normal. "    
            
        if "dischargeRate" in session.get('attributes', {}) :
            #print "***dischargeRate in session***"
            discharge_rate = session['attributes']['dischargeRate']
            speech_output += "The lake is currenty discharging to the Pomme de Terre River at a rate of " + discharge_rate + ". "
           
        if "surfaceTemp" in session.get('attributes', {}) :
            #print "***surfaceTemp in session***"
            surface_temp = session['attributes']['surfaceTemp']
            speech_output += "The lakes surface temperature is " + surface_temp + " degrees. "
            
        card_content = speech_output
        speech_output += " Please tell me what other information you would like by saying, " \
                        "tell me about the lake, tell me the history, or cancel."
        should_end_session = False
    else:
        p = MyHTMLParser()
        response = urllib2.urlopen(LAKE_URL)

        if response.getcode() == 200 : #See if response OK
            html = response.read()
            p.feed(html)
            while '\n' in p.data: p.data.remove('\n')
        
            lake_level = ''
            normal_elevation = ''
            discharge_rate = ''
            surface_temp = ''
            curr_elevation = ''
        
            for item, nxt in current_and_next(p.data):
                if item == "Normal Pool Elevation:" :
                    normal_elevation = nxt
                if item == "Lake Elevation:" :
                    curr_elevation = nxt
                if item == "Pomme de Terre River:" :
                    discharge_rate = nxt
                if item == "Lake Surface Temperature:" :
                    surface_temp = nxt.split(' ', 1)[0]
            
            p.close()
            
            if normal_elevation :
                if any(session_attributes) :
                    session_attributes['normalElevation'] = normal_elevation
                else :
                    session_attributes = create_lake_status_attributes('normalElevation', normal_elevation)
            else :
                normal_elevation = '839.00'
                
                if any(session_attributes) :
                    session_attributes['normalElevation'] = normal_elevation
                else :
                    session_attributes = create_lake_status_attributes('normalElevation', normal_elevation)
            
            if curr_elevation :
                if any(session_attributes) :
                    session_attributes['currElevation'] = curr_elevation
                else :
                    session_attributes = create_lake_status_attributes('currElevation', curr_elevation)
                speech_output = "The lakes current elavation is " + str(int(float(curr_elevation))) + " feet. "
                
                #Figure out the level
                diff = float(curr_elevation) - float(normal_elevation)
                if int(diff) > 1 :
                    level = str(int(diff)) + " feet higher "
                elif int(diff) == 1 :
                    level = str(int(diff)) + " foot higher "
                elif int(diff) == 0 :
                    level = str(int(diff)) + " feet higher "
                elif int(diff) == -1 :
                    level = str(int(diff)) + " foot lower "
                elif  int(diff) < -1 :
                    level = str(int(diff)) + " feet lower "
            
                if any(session_attributes)  :
                    session_attributes['lakeLevel'] = level
                else :
                    session_attributes = create_lake_status_attributes('lakeLevel', level)
                speech_output += "This is " + level + "than the normal pool elevation of " + str(int(float(normal_elevation))) + " feet. "
                
            if discharge_rate :
                if any(session_attributes) :
                    session_attributes['dischargeRate'] = discharge_rate
                else :
                    session_attributes = create_lake_status_attributes('dischargeRate', discharge_rate)
                speech_output += "The lake is currenty discharging to the Pomme de Terre River at a rate of " + discharge_rate + ". "
            
            if surface_temp :
                if any(session_attributes) :
                    session_attributes['surfaceTemp'] = surface_temp
                else :
                    session_attributes = create_lake_status_attributes('surfaceTemp', surface_temp)
                speech_output += "The lakes surface temperature is " + surface_temp + " degrees. "
                
            card_content = speech_output
            speech_output += "Please tell me what other information you would like by saying, " \
                "tell me about the lake, tell me the history, or cancel."
        else :
            speech_output = "There was a problem retrieving the lake information. Please try again later."
            
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, card_content, reprompt_text, should_end_session))

 
def create_lake_status_attributes(key, value):
    return {key: value}
    
 
def current_and_next(iterable):
    items, nexts = tee(iterable, 2)
    nexts = chain(islice(nexts, 1, None), [None])
    return izip(items, nexts)
 
 
def get_history_response():
    session_attributes = {}
    card_title = "History"
    speech_output = "The lake is part of a series of lakes in the Osage River Basin, designed "\
                    "and constructed by the United States Army Corps of Engineers, for flood control. "\
                    "Construction began in 1957, and was complete in 1961 at a cost of nearly 15 million dollars. "\
                    "Storage of water began on October 29, 1961, and the multipurpose pool was reached on June 15, 1963. "\
                    "Please tell me what other information you would like by saying, " \
                    "tell me about the lake, get daily information, or cancel."
    # If the user either does not reply to the welcome message or says something
    # that is not understood, they will be prompted again with this text.
    reprompt_text = "Please tell me what other information you would like by saying, " \
                    "tell me about the lake, get daily information or cancel."
    should_end_session = False
    
    card_content = speech_output
    
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, card_content, reprompt_text, should_end_session))


def get_about_response():
    session_attributes = {}
    card_title = "About"
    
    speech_output = "Pom da Terre Lake is a beautiful lake located in southwestern Missouri.  " \
                    "The lake has a surface area of nearly eight thousand acres, and 113 miles of shoreline.  " \
                    "Pom da Terre Lake is known for its Muskie, large mouth bass, croppie, and white bass fishing. " \
                    "There are over 650 campsites along the lake, as well as two public swimming beaches. " \
                    "Many forms of water recreation are common at the lake.   " \
                    "The lake is located in southern Hickory and northern Polk counties, " \
                    "about 50 miles north of Springfield. " \
                    "The name is French, and literally translated means apple from the earth, which in English is a potato. "\
                    "Please tell me what other information you would like by saying, " \
                    "tell me the history, get daily information, or cancel."
                    
    card_content = "Pomme de Terre Lake is a beautiful lake located in southwestern Missouri.  " \
                    "The lake has a surface area of nearly 8,000 acres and 113 miles of shoreline.  " \
                    "Pomme de Terre Lake is known for its Muskie, largemouth bass, crappie and white bass fishing. " \
                    "There are over 650 campsites along the lake as well as two public swimming beaches. " \
                    "Many forms of water recreation are common at the lake.   " \
                    "The lake is located in southern Hickory and northern Polk counties, " \
                    "about 50 miles north of Springfield. " \
                    "The name is French and literally translated means apple from the earth, which in English is a potato."
                    
    # If the user either does not reply to the welcome message or says something
    # that is not understood, they will be prompted again with this text.
    reprompt_text = "Please tell me what other information you would like by saying, " \
                    "tell me the history, get daily information, or cancel."
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, card_content, reprompt_text, should_end_session))


def get_welcome_response():
    session_attributes = {}
    card_title = ""
    speech_output = "Welcome to the Pom da terre lake skill. " \
                    "Please tell me what information you would like by saying, " \
                    "tell me about the lake, tell me the history, get daily information, or cancel."
    card_content = ""
    # If the user either does not reply to the welcome message or says something
    # that is not understood, they will be prompted again with this text.
    reprompt_text = "Please tell me what information you would like by saying, " \
                    "tell me about the lake, tell me the history, get daily information, or cancel."
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, card_content, reprompt_text, should_end_session))


def handle_session_end_request():
    card_title = ""
    speech_output = "Thank you for using the Pom da terre lake skill. " \
                    "Have a nice day! "
    card_content = ""
    # Setting this to true ends the session and exits the skill.
    should_end_session = True
    return build_response({}, build_speechlet_response(
        card_title, speech_output, card_content, None, should_end_session))


# --------------- Events ------------------

def on_session_started(session_started_request, session):
    """ Called when the session starts """

    print("on_session_started requestId=" + session_started_request['requestId']
          + ", sessionId=" + session['sessionId'])


def on_launch(launch_request, session):
    """ Called when the user launches the skill without specifying what they
    want
    """

    print("on_launch requestId=" + launch_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # Dispatch to your skill's launch
    return get_welcome_response()


def on_intent(intent_request, session):
    """ Called when the user specifies an intent for this skill """

    print("on_intent requestId=" + intent_request['requestId'] +
        ", sessionId=" + session['sessionId'])

    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']

    # Dispatch to your skill's intent handlers
    if intent_name == "GetDailyInfo":
        return get_daily_info(session)
    elif intent_name == "GetAbout":
        return get_about_response()
    elif intent_name == "GetHistory":
        return get_history_response()
    elif intent_name == "AMAZON.HelpIntent":
        return get_welcome_response()
    elif intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent":
        return handle_session_end_request()
    else:
        raise ValueError("Invalid intent")


def on_session_ended(session_ended_request, session):
    """ Called when the user ends the session.

    Is not called when the skill returns should_end_session=true
    """
    print("on_session_ended requestId=" + session_ended_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # add cleanup logic here


# --------------- Main handler ------------------

def lambda_handler(event, context):
    """ Route the incoming request based on type (LaunchRequest, IntentRequest,
    etc.) The JSON body of the request is provided in the event parameter.
    """
    print("event.session.application.applicationId=" +
        event['session']['application']['applicationId'])

    if (event['session']['application']['applicationId'] != "amzn1.ask.skill.5d214106-ed6d-478c-99b6-f07091943814"):
        raise ValueError("Invalid Application ID")

    if event['session']['new']:
        on_session_started({'requestId': event['request']['requestId']}, event['session'])

    if event['request']['type'] == "LaunchRequest":
        return on_launch(event['request'], event['session'])
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'], event['session'])
    elif event['request']['type'] == "SessionEndedRequest":
        return on_session_ended(event['request'], event['session'])
