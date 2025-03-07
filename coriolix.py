import requests
import json
import yaml

# Supress certificate warnings.
from urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)


class coriolix:
    
    # Class Variables:
    # Dictionary of shoreside API URLs by vessel name. 
    shoreside_api_urls = {'Point Sur': 'https://coriolix.ceoas.oregonstate.edu/point-sur/api', 
                'Endeavor': 'https://coriolix.ceoas.oregonstate.edu/endeavor/api', 
                'Sikuliaq': 'https://coriolix.sikuliaq.alaska.edu/api', 
                'Taani': 'https://taani-pub-ship.taani.oregonstate.edu/api', 
                'Narragansett Dawn': 'https://coriolix.gso.uri.edu/api', 
                'Gilbert Mason': 'https://coriolix.usm.edu/api',
                'Savannah': 'https://coriolix.skio.uga.edu/api',
                }
    # Dictionary of shipside API URLs by vessel name.
    shipside_api_urls = {'Point Sur': 'https://coriolix.ceoas.oregonstate.edu/point-sur/api', 
                'Endeavor': 'https://coriolix.ceoas.oregonstate.edu/endeavor/api', 
                'Sikuliaq': 'https://coriolix.sikuliaq.alaska.edu/api', 
                'Taani': 'https://taani-pub-ship.taani.oregonstate.edu/api', 
                'Narragansett Dawn': 'https://coriolix.gso.uri.edu/api', 
                'Gilbert Mason': 'https://coriolix.usm.edu/api',
                'Savannah': 'https://coriolix.skio.uga.edu/api',
                }

    # Constructor: Use a ship_name to lookup and set the instance varaible: api_url
    def __init__(self, ship_name, server):
        self.ship_name = ship_name
        self.server = server
        # self.api_url = self.shoreside_api_urls[ship_name]
        self.get_api_url()
        self.get_schema()
        self.get_cruises()
        self.get_sensors(enabled='true')
        self.get_sensor_parameters()

    # Build the api url
    def get_api_url(self):
       if self.server == "ship":
           self.api_url = self.shipside_api_urls[self.ship_name]
       elif self.server == "shore":
           self.api_url = self.shoreside_api_urls[self.ship_name]

    # Fetch the API schema and add it to the coriolix object
    def get_schema(self):
        query_url = self.api_url+"/schema"
        response = requests.get(query_url, verify=False)
        self.schema = yaml.load(response.text, Loader=yaml.Loader)

    # Fetch cruises and add to the coriolix object
    def get_cruises(self, id=None, start_date=None, end_date=None):

        # Get the latest cruise metadata
        if id is None and start_date is None and end_date is None:
            query_url = self.api_url+"/cruise/"
            response = requests.get(query_url, verify=False)
            self.cruise = json.loads(response.text)[0]

        elif id is not None:
            query_url = self.api_url+"/cruise/?cruise_id="+id
            response = requests.get(query_url, verify=False)
            self.cruise = json.loads(response.text)

        elif start_date is not None and end_date is not None:
            query_url = self.api_url+"/cruise/?start_date="+start_date+"&end_date="+end_date
            response = requests.get(query_url, verify=False)
            self.cruises = json.loads(response.text)

    # Get sensors and add to the coriolix object
    def get_sensors(self, enabled=None, start_date=None, end_date=None, parameters=None):

        # Workflow for getting instantaneous sensor configuration
        if start_date is None and end_date is None:
            # print("No date range specified, querying for current sensor configuration.")
 
            if enabled is None:
                # print("Fetching currently enabled and disabled sensors.")
                query_url = self.api_url+"/sensor/?enabled="
                response = requests.get(query_url, verify=False)
                # print(response.text)
                self.current_sensors = json.loads(response.text)

            elif enabled == 'true':
                # print("Fetching currently enabled sensors.")
                query_url = self.api_url+"/sensor/?enabled=true"
                response = requests.get(query_url, verify=False)
                self.currently_enabled_sensors = json.loads(response.text)

                if parameters is not None:
                    # print("Fetching sensor parameters.")
                    self.get_sensor_parameters()
                else:
                    print("No sensor parameters requested.")

            elif enabled == 'false':
                # print("Fetching currently disabled sensors.")
                query_url = self.api_url+"/sensor/?enabled=false"
                response = requests.get(query_url, verify=False)
                self.currently_disabled_sensors = json.loads(response.text)
            else:
                print("enabled argument does not match None, 'true', or 'false'")

        # Workflow for getting sensor configuration over a time interval
        elif start_date is not None and end_date is not None:
            # print("Date range specified, querying for historic sensor configuration.")

            if enabled is None:
                print("Fetching historically enabled and disabled sensors.")
                # This is a special case that returns a list of deleted/removed sensors for the time period

            elif enabled == 'true':
                print("Fetching currently enabled sensors.")
                # Get a list of all enables sensors for the time period.

            elif enabled == "false":
                print("Fetching currently disabled sensors.")
                # Get a list of all disabled sensors for the time period.

            else:
                print("enabled argument does not match None, 'true', or 'false'")
            

        elif start_date is not None and end_date is None:
            print("5")
        # Derive a comsposite list of sensors available (enabled or not)
        # For the interval defined by the start date and current time.
            pass

        else:
            print("6")
            pass

    def get_sensor_parameters(self):

        # only works for currently_enabled_sensors - flatten the get sensors method to produce only self.sensors
        for sensor in self.currently_enabled_sensors:
            query_url = self.api_url+"/parameter/?sensor_id="+sensor["sensor_id"]
            response = requests.get(query_url, verify=False)
            sensor['parameters'] = json.loads(response.text)

    def print_sensors(self):
        print(json.dumps(self.currently_enabled_sensors, indent=4))

    # Get the latest (most current) sensor observations from all sensors
    def get_last_obs(self, verbose=False):
        query_url = self.api_url+"/last_obs"
        response = requests.get(query_url, verify=False)
        if verbose==True:
            print(json.dumps(response.text, indent=4))
        self.last_obs = json.loads(response.text)
    
    def get_data(self, sensor, start_date=None, end_date=None):

        # First reduce the sensor metadata to only what is needed to make a data request
        for item in self.currently_enabled_sensors:

            if item['sensor_name']==sensor:
                sensor_name = item['sensor_name']
                sensor_parameters = {}
                par_dict = {}

                for parameter in item['parameters']:
                    long_name = parameter['long_name']
                    data_table = parameter['data_table']
                    data_field = parameter['data_fieldname']

                    par_dict[long_name] = {'data_table': data_table,
                                           'data_field': data_field}

                sensor_parameters[sensor_name] = par_dict

                for j in sensor_parameters[sensor_name]:
                    print(sensor_parameters[sensor_name][j])
