from enum import Enum
from box import Box
import logging
import portion as I

from random import randint



class BoxesType(Enum):
    CUSTOM = 1
    WORST = 2
    BALANCED = 3



"""Create graphs of working-boxes."""
class Boxes:

    def __init__ (self, depth = 1, arity = 0, kind = BoxesType.CUSTOM):
        self.boxes = []
        self.entryPoint = Box() # default entrypoint
        self.boxes.append(self.entryPoint)
        self.length = 1
        
        if (kind == BoxesType.CUSTOM):
            logging.debug("""Creating a custom graph of working-boxes. \
            Awaiting boxes to add…""")
        elif (kind == BoxesType.WORST):
            logging.debug(f"""Creating a deep unbalanced graph of \
            cascading working-boxes (d {depth}; a {arity}).""")
            buildingPoint = self.entryPoint
            inputIndex = 0
            for i in range(1, depth):
                neighbors = []
                for j in range(0, arity):
                     inputIndex = inputIndex + 1
                     self.length = self.length + 1
                     box = Box(inputIndex)
                     neighbors.append(box)
                     self.boxes.append(box)
                     buildingPoint.add_neighbor(neighbors[len(neighbors)-1])
                buildingPoint = neighbors[len(neighbors) - 1]
                     
        elif (kind == BoxesType.BALANCED):
            logging.debug(f"""Creating a balanced graph of \
            working-boxes (d {depth}; a {arity}).""")
            logging.warn("/!\ WiP /!\ ")
            ## (TODO)



    def print (self, box = None, depth = 0):
        if box is None:
            box = self.entryPoint
        tabs = ['\t'] * depth
        print ( ''.join(tabs) + box.SPRING_APPLICATION_NAME)
        for neighbor in box.remotes:
            self.print(neighbor, depth+1)



    # def addBox (self, box):
    # def addBox (self, polynome, name, neighbors):
    # def setInputGenerator ( ) :

              
    def getMaxTime (self, intervals = None):
        if intervals is None: # default
            intervals = I.closed(51,100) | I.closed(201, 250) | I.closed(351, 400)

        inputs = []
        for i in range(0, self.length):
            inputs.append(intervals.upper)
            
        return self.getTimeForInputs(inputs);
        
    def getTimeForInputs(self, inputs, box = None):
        if box is None:
            box = self.entryPoint
            
        neighbors = box.remotes
        localCost = Boxes._polynome(box.BOX_POLYNOMES_COEFFICIENTS,
                                    inputs[box.INPUT_INDEX])
        if len(neighbors) > 0:
            costs = [localCost + self.getTimeForInputs(inputs, neighbor)
                     for neighbor in neighbors]
            return max(costs)
        else:
            return localCost

    def getInput (self, intervals = None):
        whichInterval = randint(0, len( list(intervals) ) - 1) 
        minI = list(intervals)[whichInterval].lower
        maxI = list(intervals)[whichInterval].upper        
        return randint(minI, maxI)

            
    def getInputs (self, intervals = None):
        ## (TODO) create a configurable generator of inputs
        if intervals is None: # default
            intervals = I.closed(51,100) | I.closed(201, 250) | I.closed(351, 400)

        randoms = []
        for i in range(0, self.length):
            randoms.append(self.getInput(intervals))
            
        return randoms



    @staticmethod
    def _polynome (coefs, argument):
        s = 0
        for i in range(0, len(coefs)):
            s = s + coefs[i] * pow(argument, i)
        return s

