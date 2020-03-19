
port = 8080

class Box:
    def __init__(self, polynome):
        global port
        self.polynome = polynome
        self.remotes = []
        self.port = port
        self.name = 'box-' + str(self.port)
        port = port + 1

    def add(neighbors):
        self.remotes.push(neighbors)
        
