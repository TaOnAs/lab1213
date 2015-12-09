from flask import Flask, Response, render_template, request
import json
from subprocess import Popen, PIPE
from tempfile import mkdtemp
from werkzeug import secure_filename
import boto.sqs
import boto.sqs.queue
from boto.sqs.message import Message
from boto.sqs.connection import SQSConnection
from boto.exception import SQSError
import sys
import os 

app = Flask(__name__)

r = os.popen("curl -s http://ec2-52-30-7-5.eu-west-1.compute.amazonaws.com:81/key")
str = r.readline().split(':')

access_key_id = str[0]
secret_access_key = str[1]

conn = boto.sqs.connect_to_region("eu-west-1", aws_access_key_id=access_key_id, aws_secret_access_key=secret_access_key)

@app.route('/queues', methods=['GET'])
def list_queues():
    """
    List all containers
    curl -s -X GET -H 'Accept: application/json' http://localhost:5000/queues | python -mjson.tool
    """
    all = []
    for queue in conn.get_all_queues():
        all.append(queue.id)
    resp = json.dumps(all)
    return Response(response=resp, mimetype="application/json")

@app.route('/queues', methods=['POST'])
def create_queue():
    """
    Create a queue
    curl -X POST -H 'Content-Type: application/json' http://localhost:5000/queues -d '{"name": "my-queue"}'
    
    """
    body = request.get_json(force=True)
    name = body['name']
    conn.create_queue(name)
    return Response(response='{"response": "%s created"}' % name, mimetype="application/json")

@app.route('/queues/<name>', methods=['DELETE'])
def delete_queue(name):
    """
    Delete a queue
    curl -X DELETE -H 'Accept: application/json' http://localhost:5000/queues/<mytestqueue>
  
    """

    queue = conn.get_queue(name)
    conn.delete_queue(queue)
    return Response(response='{"response": "%s deleted"}' % name, mimetype="application/json")

@app.route('/queues/<name>/msgs/count', methods=['GET'])
def count_messages(name):
    """
    Get number of messages
    curl -s -X GET -H 'Accept: application/json' http://localhost:5000/queues/<name>/msgs/count | python -mjson.tool
    """
    queue = conn.get_queue(name)
    messages = queue.count()
    return Response(response='{"response": "%s messages found"}' % messages, mimetype="application/json")

@app.route('/queues/<name>/msgs', methods=['POST'])
def write_message(name):
    """
    Write a message
    curl -s -X POST -H 'Accept: application/json' http://localhost:5000/queues/<name>/msgs -d '{"content": "this is a message"}' | python -mjson.tool
    """
    body = request.get_json(force=True)
    content = body['content']
    
    queue = conn.get_queue(name)
    m = Message()
    m.set_body(content)
    queue.write(m)
    return Response(response='{"response": "Message %s written to queue"}' % content, mimetype="application/json")


@app.route('/queues/<name>/msgs', methods=['GET'])
def read_message(name):
    """
    Read a message
    curl -s -X GET -H 'Accept: application/json' http://localhost:5000/queues/<name>/msgs | python -mjson.tool
    """
    queue = conn.get_queue(name)
    m = queue.read()
    message = m.get_body()
    
    return Response(response='{"Message": "%s"}' % message, mimetype="application/json")

@app.route('/queues/<name>/msgs', methods=['DELETE'])
def consume_message(name):
    """
    Read and erase message
    curl -s -X DELETE -H 'Accept: application/json' http://localhost:5000/queues/<name>/msgs | python -mjson.tool
    """
    queue = conn.get_queue(name)
    m = queue.read()
    message = m.get_body()
    queue.delete_message(m)
    return Response(response='{"Message deleted": "%s"}' % message, mimetype="application/json")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=True)
