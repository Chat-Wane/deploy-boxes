from enum import Enum
from box import Box
import logging




class BoxesType(Enum):
    CUSTOM = 1
    WORST = 2
    BALANCED = 3



"""Create graphs of working-boxes."""
class Boxes:

    def __init__ (self, depth = 1, arity = 0, kind = BoxesType.CUSTOM):
        self.BOX_POLYNOMES_COEFFICIENTS = ['100','5']
        self.BOX_REMOTE_CALLS = ''
        self.BOX_ENERGY_THRESHOLD_BEFORE_SELF_TUNING_ARGS = '4'
        self.BOX_ENERGY_MAX_LOCAL_DATA = '10'
        self.BOX_ENERGY_FACTOR_LOCALDATAKEPT_DIFFERENTDATAMONITORED = '10'

        # default entrypoint
        self.entry = new Box(self.BOX_POLYNOMES_COEFFICIENTS)
        
        
        
        if (kind == BoxesType.CUSTOM):
            logging.debug("""Creating a custom graph of working-boxes. \
            Awaiting boxes to add…""")
        else if (kind == BoxesType.WORST):
            logging.debug(f"""Creating a deep unbalanced graph of \
            cascading working-boxes (d {depth}; a {arity}).""")                        
            for i in range(1, depth):
                
            
            ## (TODO)
        else if (kind == BoxesType.BALANCED):
            logging.debug(f"""Creating a balanced graph of \
            working-boxes (d {depth}; a {arity}).""")
            ## (TODO)
            
    def addBox (self, box):
    def addBox (self, polynome, name, neighbors):
        
    def getMaxTime (self):

    def getTimeForInputs(self, inputs):

    def getInput (self)

