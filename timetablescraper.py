
from bs4 import BeautifulSoup
import requests
import getpass
from datetime import date

#import httplib2
import os

from apiclient import discovery
import oauth2client
from oauth2client import client
from oauth2client import tools

SCOPES = 'https://www.googleapis.com/auth/calendar'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Curtin Timetable Add'

class Unit:
    def __init__(self, name, classEvents):
        self.name = name
        self.classEvents = classEvents
    
class ClassEvent:
    def __init__(self, type, start, end, day, place):
        self.type = type
        self.start = start
        self.end = end
        self.day = day
        self.place = place

def formatWhen(inString):
    return inString.replace("-", " ").split()

    
def makeClassEvent(type, when, where):
    day = when[0]
    start = [when[1], when[2]]
    end = [when[3], when[4]]
    
    return ClassEvent(type, start, end, day, where)

def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'curtin_calendar_create.json')

    store = oauth2client.file.Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials
    
class Scraper:
    def __init__(self, username, password):
        self.units = []
        
        payload = {
        'UserName' : username,
        'Password' : password,
        'submit' : 'Login' 
        }
        login_url = 'https://oasis.curtin.edu.au/Auth/LogOn'
        timetable_url = 'https://estudent.curtin.edu.au/eStudent/SM/StudentTtable10.aspx?r=%23CU.ESTU.STUDENT&f=%23CU.EST.TIMETBL.WEB'
        
        with requests.Session() as session:
            p = session.post(login_url, data = payload)
            r = session.get(timetable_url)
            data = r.text
            soup = BeautifulSoup(data, "html.parser")
        
        unitName = []
        print("Mark 2")
        for unit in soup.select('.cssTtableSspNavMasterSpkInfo2'):
            unitName.append(''.join(unit.findAll(text=True)))

        i = 0
        for unit in soup.select('.cssTtableSspNavDetailsContainerPanel'):
            events = []
            for classevent in unit.select('.cssTtableNavActvTop'):
                raw_type = classevent.select('.cssTtableSspNavActvNm')
                raw_time = classevent.select('.cssTtableNavMainWhen .cssTtableNavMainContent')
                raw_where = classevent.select('.cssTtableNavMainWhere .cssTtableNavMainContent')

                type = ''.join(raw_type[0].findAll(text=True)).strip()
                time = ''.join(raw_time[0].findAll(text=True)).strip()
                where = ''.join(raw_where[0].findAll(text=True)).strip()
                
                when = formatWhen(time)
                
                event = makeClassEvent(type, when, where)
                events.append(event)
            
            newUnit = Unit(unitName[i], events)
            self.units.append(newUnit)
            i = i + 1

def createEvent(classevent, unitname, calID):
    for classtype in classevent:
        event = {
            'summary' : unitname + ' - ' +classtype.type,
            'location' : classtype.where,
            'start' : {
                'dateTime' : classtype.start,
                'timeZone' : 'Australia/Perth'
            },
            'end' : {
                'dateTime' : classtype.end,
                'timeZone' : 'Australia/Perth'
            },
                'recurrence' : [
                    'RRULE:FREQ=DAILY;COUNT=12'
            ],
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method' : 'popup', 'minutes': 10}
                ]
            }
        }
        
        event = service.events().insert(calendarId=calID, body=event).execute()
        
def createCalendar(creds):
    calendar = {
    'summary': 'Curtin Class Timetable',
    'timeZone': 'Australia/Perth'
    }

    created_calendar = service.calendars().insert(body=calendar).execute()
    
    return created_calendar['id']
    
def addToCalendar():
    creds = get_credentials()
    cal_id = createCalender(creds)
    
    for unit in units:
        for event in unit:
            createEvent(event, unit.unitname, cal_id)  
        
if __name__ == '__main__':
    
    username = input("Student ID: ")
    password = getpass.getpass()
    
    scraper = Scraper(username, password)
    
