
port = 9000

class Box:
    def __init__(self, polynome):
        global port
        self.polynome = polynome
        self.remotes = []
        self.port = port
        port = port + 1
        self.name = 'box-' + str(self.port)

    def add(neighbors):
        self.remotes.push(neighbors)
        
