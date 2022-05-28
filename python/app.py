import json

from gevent import monkey

monkey.patch_all()
import logging
import os
from flask import Flask, jsonify, request
from raft.cluster import Cluster
from timer_thread import TimerThread

logging.basicConfig(format='%(asctime)s - %(levelname)s: %(message)s', datefmt='%H:%M:%S', level=logging.INFO)

NODE_ID = int(os.environ.get('NODE_ID'))

cluster = Cluster()

node = cluster[NODE_ID]
# Node(0, localhost:5000)
# Node(1, localhost:5001)
# Node(2, localhost:5002)
# Node(3, localhost:5003)
# Node(4, localhost:5004)

timer_thread = TimerThread(NODE_ID)
# TimerThread(0)
# TimerThread(1)
# TimerThread(2)
# TimerThread(3)
# TimerThread(4)

def create_app():
    raft = Flask(__name__)
    timer_thread.start()
    return raft


app = create_app()


@app.route('/raft/vote', methods=['POST'])
def request_vote():
    vote_request = request.get_json()
    result = timer_thread.vote(json.loads(vote_request))
    return jsonify(result)


@app.route('/raft/heartbeat', methods=['POST'])
def heartbeat():
    leader = request.get_json()
    logging.info(f'{timer_thread} got heartbeat from leader: {leader}')
    d = {"alive": True, "node": node}
    timer_thread.become_follower()
    return jsonify(d)


@app.route('/')
def hello_raft():
    return f'raft cluster: {cluster}!'


if __name__ == '__main__':
    create_app()
    app.run()

# NODE_ID=0 python -p 5000 app.py
# NODE_ID=1 python -p 5001 app.py
# NODE_ID=2 python -p 5002 app.py
# NODE_ID=3 python -p 5003 app.py
# NODE_ID=4 python -p 5004 app.py
