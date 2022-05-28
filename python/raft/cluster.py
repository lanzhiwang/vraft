import collections

Node = collections.namedtuple('Node', ['id', 'uri'])
CLUSTER_SIZE = 5
ELECTION_TIMEOUT_MAX = 10
HEART_BEAT_INTERVAL = float(ELECTION_TIMEOUT_MAX/5)


class Cluster:
    ids = range(0, CLUSTER_SIZE)  # [0 1 2 3 4]
    uris = [f'localhost:500{n}' for n in ids]  # [localhost:5000 localhost:5001 localhost:5002 localhost:5003 localhost:5004]

    def __init__(self):
        self._nodes = [Node(nid, uri) for nid, uri in enumerate(self.uris, start=0)]
        # Node(0, localhost:5000)
        # Node(1, localhost:5001)
        # Node(2, localhost:5002)
        # Node(3, localhost:5003)
        # Node(4, localhost:5004)


    def __len__(self):
        return len(self._nodes)

    def __getitem__(self, index):
        return self._nodes[index]

    def __repr__(self):
        return ", ".join([f'{n.id}@{n.uri}' for n in self._nodes])


if __name__ == '__main__':
    cluster = Cluster()
    print(cluster)
