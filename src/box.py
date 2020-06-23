
port = 8080



class Box:
    def __init__(self,
                 input_index = 0, polynome = [100,5],
                 threshold = 4, local_data = 10, factor = 10):
        global port
        self.BOX_POLYNOMES_COEFFICIENTS = polynome
        self.INPUT_INDEX = input_index
        self.BOX_REMOTE_CALLS = []
        self.BOX_ENERGY_THRESHOLD_BEFORE_SELF_TUNING_ARGS = threshold
        self.BOX_ENERGY_MAX_LOCAL_DATA = local_data
        self.BOX_ENERGY_FACTOR_LOCALDATAKEPT_DIFFERENTDATAMONITORED = factor

        self.SERVER_PORT = port
        self.SPRING_APPLICATION_NAME = f'box-{self.SERVER_PORT}'
        port = port + 1

        self.remotes = []

    # def add(self, neighbors):
    #     remotes = []
    #     for box, progress in neighbors:
    #         remotes.append('http://localhost:{}@{}'.format(box.port, progress))
    #     if len(remotes) > 0:
    #         self.remotes = ','.join(remotes)
    #     return self

    def add_neighbor (self, box) :
        self.remotes.append(box)
    
    def POLYNOME (self) :
        return ','.join([str(coef) for coef in self.BOX_POLYNOMES_COEFFICIENTS]) + '@' + str(self.INPUT_INDEX)

    def REMOTE_CALLS (self, boxNameToAddress):
        addresses = ['http://'+ boxNameToAddress[box.SPRING_APPLICATION_NAME] +
                     ':' + str(box.SERVER_PORT) + '@100'
                     for box in self.remotes]
        return ','.join(addresses)
