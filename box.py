
port = 8080

class Box:
    def __init__(self, polynome):
        global port
        self.polynome = polynome
        self.remotes = []
        self.port = port
        self.name = 'box-' + str(self.port)
        port = port + 1
        # 160 is out of bound so it does nothing
        self.remotes = 'http://nothing:3615@160'
        

    def add(self, neighbors):
        remotes = []
        for box, progress in neighbors:
            remotes.append('http://localhost:{}@{}'.format(box.port, progress))
        if len(remotes) > 0:
            self.remotes = ','.join(remotes)
            
        
