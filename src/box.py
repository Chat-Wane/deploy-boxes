
port = 8080

class Box:
    def __init__(self, polynome):
        global port
        self.polynome = polynome
        self.remotes = []
        self.port = port
        self.name = 'box-' + str(self.port)
        port = port + 1

    def add(self, neighbors):
        remotes = []
        for box, progress in neighbors:
            remotes.append('http://localhost:{}@{}'.format(box.port, progress))
        self.remotes = ','.join(remotes)
        print(self.remotes)
            
        
