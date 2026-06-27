import requests
import uuid
import json
import os
import time

def _form_request():
    rq_uid = str(uuid.uuid4())
    filename = 'get_access_token.json'

    with open(filename, 'r') as data:
      params = json.load(data)

    headers = {
      'Content-Type': 'application/x-www-form-urlencoded',
      'Accept': 'application/json',
      'RqUID': rq_uid,
      'Authorization': f'Bearer {params["auth_data"]}'
    }

    try:
        response = requests.request("POST", params['url'], 
                                    headers=headers, 
                                    data=params['payload'], 
                                    verify=params['cert_path'])
        response_json = response.json()
        with open('access_token.json', 'w') as acj:
          json.dump(response_json, acj)
        return response_json
    except requests.exceptions.RequestException as re:
        print("Error: ", re)

def get_access_token():
    token_file = 'access_token.json'
    if not os.path.exists(token_file) or os.path.getsize(token_file) == 0:
        response_json = _form_request()
        return response_json if response_json else None
    with open(token_file, 'r') as acj:
        data = json.load(acj)
    if data['expires_at'] > int(time.time() * 1000):
        return data
    else:
        return response_json if response_json else None

print(get_access_token())