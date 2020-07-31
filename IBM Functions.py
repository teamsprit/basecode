#
#
# main() will be run when you invoke this action
#
# @param Cloud Functions actions accept a single parameter, which must be a JSON object.
#
# @return The output of this action, which must be a JSON object.
#

import sys
import json
import base64
from cloudant.client import Cloudant
from cloudant.error import CloudantException
from cloudant.result import Result, ResultByKey
from cloudant.document import Document
from datetime import datetime as dt

def raise_request(username,my_database):
    result_collection = Result(my_database.all_docs , include_docs=True )
    request_already_available = False
    try:
        for i in result_collection:
            if 'username' in i['doc']:
                if str(i['doc']['username']).lower() == username.lower():
                    if i['doc']['status'] == 'inprogress' or i['doc']['status'] == 'pending_approval':
                        return f"Request {i['doc']['request_number']} already raised for you, it will be delivered within 1 week from the date of request raised", False
        selector = {'type': {'$eq': 'latest_request_number'}}
        docs = my_database.get_query_result(selector)

        for doc in docs:
            # Create Document object from dict
            updated_doc = Document(my_database, doc['_id'])
            updated_doc.update(doc)
            latest_request_number = updated_doc['number']+1
            # Update document field
            updated_doc['number'] = latest_request_number
            # Save document
            updated_doc.save()
                
        if not request_already_available:
            json_document = {
                "username": username,
                "request_number": latest_request_number,
                "status" : "pending_approval",
                "Create_time" :str(dt.now()),
                "esacalate" : "no"
                }
            new_document = my_database.create_document(json_document)
            if new_document.exists():
                return f"Request : '{latest_request_number}' successfully created for you. Laptop would be delivered in 1 week", True
        
    except Exception as e1:
        err_msg= "unable to raise request due to err " + str(e1) + ", please try after some time", False
        return err_msg, True

def get_status(username,my_database):
    result_collection = Result(my_database.all_docs , include_docs=True )
    try:
        for i in result_collection:
            if 'username' in i['doc']:
                if str(i['doc']['username']).lower() == username.lower():
                    if i['doc']['status'] == 'inprogress' or i['doc']['status'] == 'pending_approval':
                        return f"Request : {i['doc']['request_number']} already raise for you, it will be delivered within 1 week from the request", True
                    else:
                        return f"Request is already in {i['doc']['status']} status, plase raise a new request for fresh laptop", False
        return f"There are no requests avaliable in your name, do you like to raise now" , False
    except Exception as e1:
        err_msg= "unable to raise request due to err " + str(e1) + ", please try after some time"
        return err_msg, True
        
def get_general_covid_data(input_text,primary): 
    import requests
    url="https://api.covid19api.com/summary"
    requests.get(url)
    response = requests.get(url)
    if response.status_code<300:
        data = response.json()
        global_data = data['Global']
        result = f"Total Cases: {global_data['TotalConfirmed']}\nTotal Deaths: {global_data['TotalDeaths']}\nTotal Recovered: {global_data['TotalRecovered']}\n\nSource: Johns Hopkins CSSE\n\n Would you like the stats of a specific Country?"
        country = 'globally'
        each_words = input_text.split(" ")
        for i in each_words:
            for j in data['Countries']:
                if str(j['Country']).lower() == str(i).lower():
                    global_data = j
                    result = f"Total Cases: {global_data['TotalConfirmed']}\nTotal Deaths: {global_data['TotalDeaths']}\nTotal Recovered: {global_data['TotalRecovered']}\n\nSource: Johns Hopkins CSSE\n\n"
                    country =  j['Country']
                    if primary == "yes":
                        result = result + "Would you like the stats of any other Country?"
                    return result, country
        if primary == "yes":
            return result, country
        else:
            raise Exception("request didn't go through")
    else:
        raise Exception("request didn't go through")

def get_location_status_latlong(lat,lon):
    try:
        import requests,json
        url="https://data.geoiq.io/dataapis/v1.0/covid/locationcheck"
        data = {}
        data["key"]="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJtYWlsSWRlbnRpdHkiOiJuYW5kYWdjZWJAZ21haWwuY29tIn0.N1-ZSx-PA5ZNXLTbBuWNPCNfUiZOZtQHiSuYcI9xK9g"
        data["latlngs"]=[]
        data["latlngs"].append([float(lat),float(lon)])
        response = requests.post(url,data=json.dumps(data))
        if response.status_code<300:
            data1 = response.json()
            if data1['data'][0]['inContainmentZone']:
                return "You are in containment zone, please avoid travelling to office"
            else:
                return f"Good to know that your location \n latitude : {lat}\n longitude: {lon}\nis in safe zone, you can travel to office without any issues. \n\nplease check office operational status every day on internal NEWS channel before commuting"
        return f"unable to process your request, please try again after sometime lat {lat} : lon {lon}"
    except Exception as e1:
        err_msg = "unable to process your request due to error: " + str(e1) +" , please try after some time"
        return err_msg
    
def get_location_status_zipcode(zipcode):
    try:
        import requests, json
        """
        url="http://geocode.xyz/"
        final_url =  url+str(zipcode)+"?region=IN&json=1"
        for i in range(0,3):
            response = requests.get(final_url)
            if response.status_code<300:
                data = response.json()
                lat = data['longt']
                lon = data['latt']
                message_body = get_location_status_latlong(lat,lon)
                return message_body
            import time
            time.sleep(1)
        
        """
        url="https://data.geoiq.io/dataapis/v1.0/covid/pincodecheck"
        data = {}
        data["key"]="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJtYWlsSWRlbnRpdHkiOiJuYW5kYWdjZWJAZ21haWwuY29tIn0.N1-ZSx-PA5ZNXLTbBuWNPCNfUiZOZtQHiSuYcI9xK9g"
        data["pincode"] = str(zipcode)
        response = requests.post(url,data=json.dumps(data))
        if response.status_code<300:
            data1 = response.json()
            if 'data'in data1:
                if data1['data']['hasContainmentZone']:
                    return f"You ZIPCODE:{zipcode} locality have containment zone's, please avoid travelling to office"
                else:
                    return "Good to know that you are in safe zone, you can travel to office without any issues. \n\nplease check office operational status every day on internal NEWS channel before commuting"
            else:
                if 'status' in data1:
                    return "unable to process your request due to error in source api"
                else:
                    return "unable to process your request due to unknown error in api"
        
        return "unable to process your request, please try again after sometime zipcode"
    except Exception as e1:
        err_msg = "unable to process your request due to error: " + str(e1) +" , please try after some time : "+ str(response.text)
        return err_msg
        
def get_dashboard_Stats(my_database):
    selector = {'request_number': {'$gt': 10000}}
    docs = my_database.get_query_result(selector)
    completed=0
    inprogress=0
    rejected=0
    for doc in docs:
        updated_doc = Document(my_database, doc['_id'])
        updated_doc.update(doc)
        if updated_doc['status'] == "completed":
            completed+=1
        elif updated_doc['status'] == "pending_approval" or updated_doc['status'] =="inprogress":
            inprogress+=1
        elif updated_doc['status'] == "rejected":
            rejected+=1        
    return completed, inprogress,rejected

def main(dict):
    
    client=Cloudant.iam("0fd95ac4-2ac0-431b-81d6-262ddb8f96a2-bluemix","GcFI2eASYsVedpBzjNShcXUdbRIgJ3tK64uXREh23OI3")
    client.connect()
    my_database= client['training']
    status = True
    try:
        message_body = "unable to get the exact data, please contact after some time"
        params = json.loads(base64.b64decode(dict['__ow_body']).decode('utf-8'))
        request_type = str(params['request_type'])
        if request_type.lower() == "raise":
            username = str(params['username'])
            message_body , status  = raise_request(username,my_database)
        elif request_type.lower() ==  "get_status":
            username = str(params['username'])
            message_body , status = get_status(username,my_database)
        elif request_type.lower() ==  "get_general_covid_data":
            input_text = str(params['input'])
            primary = str(params['primary'])
            message_body, country = get_general_covid_data(input_text,primary)
            return {"result" :  message_body , "country" : country}
        elif request_type.lower() ==  "get_location_status_latlong":
            message_body = get_location_status_latlong(params['latitude'],params['longitude'])
            return {"message" : message_body}
        elif request_type.lower() ==  "get_location_status_zipcode":
            message_body = get_location_status_zipcode(params['zipcode'])
            return {"message" : message_body}
        elif request_type.lower() ==  "get_dashboard_stats":
            completed, inprogress,rejected = get_dashboard_Stats(my_database)
            data = {}
            data['values']=[completed, inprogress,rejected]
            data1 = json.dumps(data)
            client.disconnect()
            return data
        elif request_type.lower() ==  "get_approval_requests":
            return {}
        else:
            return {"message" : "Unknown format type, please check with administrator."}
            
    except Exception as e1:
        message_body = "unable to process your request due to error: " + str(e1) + ", please try after some time "
    
    client.disconnect()
    if status:
        return { 'message': message_body ,'valid' : status}
    else:
        return { 'message': message_body }
