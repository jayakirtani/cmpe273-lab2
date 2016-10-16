
import logging
logging.basicConfig(level=logging.DEBUG)
import requests
import re
from datetime import datetime
from spyne import Application, rpc, ServiceBase, \
    Integer, Unicode , String, Double

#from spyne import Iterable
from spyne.decorator import srpc

from spyne.protocol.http import HttpRpc
from spyne.protocol.json import JsonDocument
from spyne.server.wsgi import WsgiApplication

class HelloWorldService(ServiceBase):

 
    @srpc(Double,Double,Double, _returns = String)
    def checkcrime(lat,lon,radius):
        payload={'lat' : lat,'lon' : lon , 'radius':radius ,'key':'.'}
        print payload
        url = 'https://api.spotcrime.com/crimes.json'
        req = requests.get(url,params=payload)
        print req.status_code
        if req.status_code !=200 :
            return "Unable to connect to Spot crime API"
        data = req.json()
        crimetypecount = {}
        eventtimecount = { "12:01am-3am" : 0,
                            "3:01am-6am" : 0,
                            "6:01am-9am" : 0,
                            "9:01am-12noon" : 0,
                            "12:01pm-3pm" : 0,
                            "3:01pm-6pm" : 0,
                            "6:01pm-9pm" : 0,
                            "9:01pm-12midnight" : 0
                        } 
        totalCrime = 0;   
        crimeatlocation={}   
        pattmatch = re.compile('(?:((?:\b\D\b ){0,1}(?:\w+ )*\w+ (?:ST|AVE|AV|LN|WAY|BL)) &)* ((?:\b\D\b ){0,1}(?:\w+ )*\w+ (?:ST|AVE|AV|LN|WAY|BL))$')    

        def crimelocation(location) :

            location=location.replace("BLOCK","")
            location=location.replace("OF","")
            location=location.strip()
            
            if (crimeatlocation.has_key(location)):
                crimeatlocation[location] = crimeatlocation[location]+1
            else :
                crimeatlocation[location] = 1


        for crime in data["crimes"]:

            # Count total crime
            totalCrime+=1

            # Count different type of crimes
            crimetype=crime["type"]
            if (crimetypecount.has_key(crimetype)):
                crimetypecount[crimetype] = crimetypecount[crimetype]+1
            else :
                crimetypecount[crimetype] = 1
             
            # Count number of crimes in a specified time range
            crimedate = datetime.strptime(crime["date"],"%m/%d/%y %I:%M %p")
            #convert the time into 24 hr format for easier conparison 
            crimetime = int(crimedate.strftime("%H%M"))
    
            if (crimetime >= 0001 and crimetime <=300):
                eventtimecount["12:01am-3am"]+=1
            elif (crimetime >= 301 and crimetime <=600):
                eventtimecount["3:01am-6am"]+=1
            elif (crimetime >= 601 and crimetime <=900):
                eventtimecount["6:01am-9am"]+=1
            elif (crimetime >= 901 and crimetime <=1200):
                eventtimecount["9:01am-12noon"]+=1        
            elif (crimetime >= 1201 and crimetime <=1500):
                eventtimecount["12:01pm-3pm"]+=1
            elif (crimetime >= 1501 and crimetime <=1800):
                eventtimecount["3:01pm-6pm"]+=1 
            elif (crimetime >= 1801 and crimetime <=2100):
                eventtimecount["6:01pm-9pm"]+=1
            elif ((crimetime >= 2101 and crimetime <=2359) or crimetime == 0000 ):
                eventtimecount["9:01pm-12midnight"]+=1      

            #Count crime at location
            for street in pattmatch.finditer(crime["address"]):
                if (street.group(1)):
                    crimelocation(street.group(1))
                if (street.group(2)):
                    crimelocation(street.group(2))                       

        #Find top three streets according to highest crimes
        sortedlist =  sorted(crimeatlocation, key=crimeatlocation.__getitem__,reverse=True)
        topstreet=[]
        if (len(sortedlist) >3) :
            topstreet.append(sortedlist[0])
            topstreet.append(sortedlist[1])
            topstreet.append(sortedlist[2])
        else :
             topstreet = sortedList   
        print topstreet
        crimeSummary = {"total_crime" : totalCrime,
                        "the_most_dangerous_streets" : topstreet,
                        "crime_type_count" : crimetypecount,
                        "event_time_count" : eventtimecount
        }
        
        return crimeSummary
        

application = Application([HelloWorldService],
    tns = 'cmpe273.lab2',
    in_protocol=HttpRpc(validator='soft'),
    out_protocol=JsonDocument()
)

if __name__ == '__main__':
    # You can use any Wsgi server. Here, we chose
    # Python's built-in wsgi server but you're not
    # supposed to use it in production.
    from wsgiref.simple_server import make_server

    wsgi_app = WsgiApplication(application)
    server = make_server('0.0.0.0', 8000, wsgi_app)
    server.serve_forever()