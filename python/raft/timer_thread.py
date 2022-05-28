import sys
import threading
from random import randrange
import logging

from monitor import send_state_update

logging.basicConfig(format='%(asctime)s - %(levelname)s: %(message)s', datefmt='%H:%M:%S', level=logging.INFO)

from Candidate import Candidate, VoteRequest
from Follower import Follower
from Leader import Leader
from cluster import Cluster, ELECTION_TIMEOUT_MAX

cluster = Cluster()

# TimerThread(0)
# TimerThread(1)
# TimerThread(2)
# TimerThread(3)
# TimerThread(4)
class TimerThread(threading.Thread):
    def __init__(self, node_id):
        threading.Thread.__init__(self)
        self.node = cluster[node_id]
        # Node(0, localhost:5000)
        # Node(1, localhost:5001)
        # Node(2, localhost:5002)
        # Node(3, localhost:5003)
        # Node(4, localhost:5004)

        self.node_state = Follower(self.node)
        self.election_timeout = float(randrange(ELECTION_TIMEOUT_MAX / 2, ELECTION_TIMEOUT_MAX))
        self.election_timer = threading.Timer(self.election_timeout, self.become_candidate)

    def become_leader(self):
        logging.info(f'{self} become leader and start to send heartbeat ... ')
        send_state_update(self.node_state, self.election_timeout)
        self.node_state = Leader(self.node_state)
        self.node_state.heartbeat()

    def become_candidate(self):
        logging.warning(f'heartbeat is timeout: {int(self.election_timeout)} s')
        logging.info(f'{self} become candidate and start to request vote ... ')

        # TODO
        send_state_update(self.node_state, self.election_timeout)

        # 将节点状态变为 Candidate，并开始选举
        self.node_state = Candidate(self.node_state)
        # 向其他节点发送选举请求
        self.node_state.elect()
        if self.node_state.win():
            self.become_leader()
        else:
            self.become_follower()

    # input: candidate (id, term, lastLogIndex, lastLogTerm)
    # output: term, vote_granted
    # rule:
    #   1. return false if candidate.term < current_term
    #   2. return true if (voteFor is None or voteFor==candidate.id) and candidate's log is newer than receiver's

    # 处理其他节点发送的选举请求，此时其他节点的状态可能是 Leader，Follower，Candidate
    # vote(json.loads(vote_request))
    def vote(self, vote_request: VoteRequest):
        logging.info(f'{self} got vote request: {vote_request} ')
        vote_result = self.node_state.vote(vote_request)
        if vote_result[0]:
            self.become_follower()
        logging.info(f'{self} return vote result: {vote_result} ')
        return vote_result

    # 当节点刚启动时，节点会自动变为 Follower 状态，会由这个函数处理 Follower 状态
    # 当 leader 发送了心跳请求，也会由这个函数处理心跳请求
    def become_follower(self):
        timeout = float(randrange(ELECTION_TIMEOUT_MAX / 2, ELECTION_TIMEOUT_MAX))
        # 当该节点已经是 Follower 节点，但 Leader 节点不向他发送心跳信息时
        # 这是该节点没有必要再次改变节点角色，只需要等心跳超时时间超时就变为 Candidate 节点发起投票请求
        if type(self.node_state) != Follower:
            logging.info(f'{self} become follower ... ')
            self.node_state = Follower(self.node)
        logging.info(f'{self} reset election timer {timeout} s ... ')

        # TODO
        send_state_update(self.node_state, timeout)

        # 第一次没有 Leader 节点发送心跳信息时，肯定会超时
        # 后面当收到 Leader 节点发送心跳信息时，需要将 election_timer 线程取消，然后再次启动 election_timer 线程，等待下次超时
        self.election_timer.cancel()
        # threading.Timer(超时时间，超时之后执行的函数)
        # 当有一个节点超时之后，超时的节点会变为 Candidate 节点
        self.election_timer = threading.Timer(timeout, self.become_candidate)
        self.election_timer.start()

    def run(self):
        self.become_follower()

    def __repr__(self):
        return f'{type(self).__name__, self.node_state}'


if __name__ == '__main__':
    timerThread = TimerThread(int(sys.argv[1]))
    timerThread.start()
