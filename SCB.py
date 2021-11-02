#Server Control Block: just keeps track of server info
class SCB:
    def __init__(self,ip, port):
        self.ip = ip
        self.port = port
        self.totalReqs = 0
        self.totalData = 0