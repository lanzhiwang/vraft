import json

import grequests
from NodeState import NodeState
from client import Client
import logging

logging.basicConfig(format='%(asctime)s - %(levelname)s: %(message)s', datefmt='%H:%M:%S', level=logging.INFO)


class VoteRequest:
    def __init__(self, candidate):
        self.candidate_id = candidate.id
        self.term = candidate.current_term
        # TODO initialize log info when implement raft log replication
        self.last_log_index = 0
        self.last_log_term = 0

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__,
                          sort_keys=True, indent=4)


# Follower(Node(0, localhost:5000))
# Follower(Node(1, localhost:5001))
# Follower(Node(2, localhost:5002))
# Follower(Node(3, localhost:5003))
# Follower(Node(4, localhost:5004))
# Candidate(Follower(Node(0, localhost:5000)))
class Candidate(NodeState):
    """ The state of candidate

    The service will become candidate if no heartbeat is heard from leader
    after the election timeout comes.

    Candidate will start a new leader election with current_term+1.
    If the candidate can get quorum votes before the election timeout comes,
    it becomes the leader and send heartbeat to followers immediately.
    Otherwise, start a new election with current_term+1.
    TODO add pre election later
    """

    def __init__(self, follower):
        super(Candidate, self).__init__(follower.node)
        self.current_term = follower.current_term
        self.commit_index = follower.commit_index
        self.last_applied_index = follower.last_applied_index
        self.votes = []
        self.entries = follower.entries
        self.followers = [peer for peer in self.cluster if peer != self.node]

        # 该节点是 Candidate 节点，他会先投自己一票
        self.vote_for = self.id  # candidate always votes itself

    # 向其他节点发送选举请求
    def elect(self):
        """ When become to candidate and start to elect:
            1. term + 1
            2. vote itself
            3. send the vote request (VR) to each peer in parallel
            4. return when it is timeout
        """
        self.current_term = self.current_term + 1
        logging.info(f'{self} sends vote request to peers ')
        # vote itself
        self.votes.append(self.node)
        client = Client()
        with client as session:
            posts = [  # VoteRequest(self)
                grequests.post(f'http://{peer.uri}/raft/vote', json=VoteRequest(self).to_json(), session=session)
                for peer in self.followers
            ]
            for response in grequests.imap(posts):
                logging.info(f'{self} got vote result: {response.status_code}: {response.json()}')
                result = response.json()  # VoteResult(False, self.current_term, self.id)
                if result[0]:  # vote_granted
                    self.votes.append(result[2])  # id

    # 判断自己是否赢得选举
    def win(self):
        return len(self.votes) > len(self.cluster) / 2

    def __repr__(self):
        return f'{type(self).__name__, self.node.id, self.current_term}'
