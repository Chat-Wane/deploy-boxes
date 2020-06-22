from boxes import Boxes, BoxesType



boxes = Boxes(depth=3, arity=2, kind=BoxesType.WORST)

boxes.print()

inputs = boxes.getInputs()
print(inputs)

longestTime = boxes.getTimeForInputs(inputs)
print(longestTime)

longestTimeOfLongest = boxes.getMaxTime()
print(longestTimeOfLongest)



