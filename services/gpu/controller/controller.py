from google.auth import compute_engine
from googleapiclient import discovery
from flask import Flask, request, jsonify
import random
import string
import time

app = Flask(__name__)

# generators
def id_generator(size=4, chars=string.ascii_lowercase + "labs"):
    return ''.join(random.choice(chars) for _ in range(size))

def password_generator(size=12, chars=string.ascii_lowercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

# get the token from gcp tag on instance
import httplib2
http = httplib2.Http()
url = 'http://metadata.google.internal/computeMetadata/v1/instance/tags'
headers = {'Metadata-Flavor': 'Google'}
response, content = http.request(url, 'GET', headers=headers)
evalcontent = eval(content)
for item in evalcontent:
        if 'token' in item:
            key,token = item.split('-')

# google creds
credentials = compute_engine.Credentials()
compute = discovery.build('compute', 'v1', credentials=credentials)
compute_beta = discovery.build('compute', 'beta', credentials=credentials)

# project and zones
project = 'sloth-ai'
zones = ['us-central1-a']


@app.route('/api/instance/list', methods=['GET'])
def list_instances():
    try:
        if request.args.get('token') != token:
            return jsonify({'error': "need token"})
    except:
        return jsonify({'error': "need token"})

    try:
        items = []
        for z in zones:
            for x in range(3):
                try:
                    result = compute.instances().list(
                        project=project,
                        zone=f'{z}'
                    ).execute()
                    break
                except Exception as ex:
                    print(ex)
                    print("sleeping...")
                    time.sleep(3)
                    print("waking...")

            try:
                for item in result['items']:
                    items.append(item)
            except:
                print(f"{z} has no instances or does not exist")
        return jsonify(items)
    except:
        print("error: %s" % ex)
        return jsonify([])


@app.route('/api/instance/<zone>/<instance_id>/status', methods=['GET'])
def instance_status(zone, instance_id):
    try:
        if request.args.get('token') != token:
            return jsonify({'error': "need token"})
    except:
        return jsonify({'error': "need token"})

    try:
        result = compute.instances().get(
            project=project,
            zone=zone,
            instance=instance_id
        ).execute()

    except Exception as ex:
        if "HttpError" in str(ex):
            result = {'error': "NOTFOUND"}
        else:
            result = {'error': f"{ex}"}

    return jsonify(result)


@app.route('/api/instance/<zone>/<instance_id>/start', methods=['GET'])
def start_instance(zone, instance_id):
    try:
        if request.args.get('token') != token:
            return jsonify({'error': "need token"})
    except:
        return jsonify({'error': "need token"})

    try:
        result = compute.instances().start(
            project=project,
            zone=zone,
            instance=instance_id
        ).execute()
    except Exception as ex:
        print("error: %s" % ex)
    return jsonify(result)


@app.route('/api/instance/<zone>/<instance_id>/stop', methods=['GET'])
def stop_instance(zone, instance_id):
    try:
        if request.args.get('token') != token:
            return jsonify({'error': "need token"})
    except:
        return jsonify({'error': "need token"})

    try:
        result = compute.instances().stop(
            project=project,
            zone=zone,
            instance=instance_id
        ).execute()
    except Exception as ex:
        print("error: %s" % ex)
    return jsonify(result)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
