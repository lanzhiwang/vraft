import collections

from cluster import Cluster
import logging

logging.basicConfig(format='%(asctime)s - %(levelname)s: %(message)s', datefmt='%H:%M:%S', level=logging.INFO)

VoteResult = collections.namedtuple('VoteResult', ['term', 'vote_granted', 'id'])


# NodeState(Node(0, localhost:5000))
# NodeState(Node(1, localhost:5001))
# NodeState(Node(2, localhost:5002))
# NodeState(Node(3, localhost:5003))
# NodeState(Node(4, localhost:5004))
class NodeState:
    def __init__(self, node=None):
        self.cluster = Cluster()
        self.node = node

        self.id = node.id
        self.current_term = 0

        # 需要记录该节点是否在这个 term 内已经投过一票了，如果投过就不允许再投
        self.vote_for = None  # node.id of the voted candidate

    # input: candidate (id, current_term, lastLogIndex, lastLogTerm)
    # output: vote_granted (true/false), term (current_term, for candidate to update itself)
    # rule:
    #   1. return false if candidate.term < current_term
    #   2. return true if (voteFor is None or voteFor==candidate.id) and candidate's log is newer than receiver's

    # 处理其他节点发送的选举请求，通过判断任期进行投票
    # vote_request{
    #     "candidate_id" = candidate.id
    #     "term" = candidate.current_term
    #     "last_log_index" = 0
    #     "last_log_term" = 0
    # }
    def vote(self, vote_request):
        term = vote_request['term']
        candidate_id = vote_request['candidate_id']
        if term > self.current_term:
            logging.info(f'{self} approves vote request since term: {term} > {self.current_term}')
            self.vote_for = candidate_id
            self.current_term = term
            return VoteResult(True, self.current_term, self.id)
        if term < self.current_term:
            logging.info(f'{self} rejects vote request since term: {term} < {self.current_term}')
            return VoteResult(False, self.current_term, self.id)
        # vote_request.term == self.current_term
        if self.vote_for is None or self.vote_for == candidate_id:
            # TODO check if the candidate's log is newer than receiver's
            self.vote_for = candidate_id
            return VoteResult(True, self.current_term, self.id)
        logging.info(f'{self} rejects vote request since vote_for: {self.vote_for} != {candidate_id}')
        return VoteResult(False, self.current_term, self.id)

    # another thread might change the state into Follower when got heartbeat
    # only candidate could return True
    # it returns False for both Leader and Follower
    def win(self):
        return False
