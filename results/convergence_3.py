import json
import sys
from pathlib import Path
from io import BytesIO



TRACES_FILES = [Path('result_convergence_3_s17.json'),
                Path('result_convergence_3_s18.json'),
                Path('result_convergence_3_s19.json')]
                # Path('result_convergence_3_s4.json')]



def _getTag(name, tags):
    for tag in tags:
        if (tag['key'] == name):
            return tag['value']
    return None
                                    
kepts = []
errors = []
rewrittens = []
for TRACES_FILE in TRACES_FILES:
    if not TRACES_FILE.is_file():
        print ("/!\ The file you try to analyze does not exist.")
        sys.exit(0)

        
    with TRACES_FILE.open('r') as f:
        results = json.load(f)
        
        traces = []
        for trace in results['data']:
            isValidTrace = False
            starttimes = []
            for span in trace['spans']:
                if (span['operationName'] == 'handle'):
                    isValidTrace = True
                    starttimes.append(span['startTime'])
                    
            if isValidTrace:
                traces.append((min(starttimes), trace))

        traces = sorted(traces, key=lambda x: x[0])



        i = 0
        for trace in [kv[1] for kv in traces]:
            front = None
            for process in trace['processes']:
                if (trace['processes'][process]['serviceName'] == 'box-8080'):
                    front = process
                    
            globalObjective = 0            
            sumOfCosts = 0
            sumOfRewritten = 0
            sumOfKept = 0                       
            for span in trace['spans']:
                if (span['operationName'] == 'handle'):                    
                    tags = span['tags']
                    sumOfCosts = sumOfCosts + span['duration'] / 1000
                    if (span['processID'] == front): ## handle@box-8080
                        globalObjective = _getTag('objective', tags)
                    
                    isLastInputKept = _getTag('isLastInputKept', tags)
                    isLastInputRewritten = _getTag('isLastInputRewritten', tags)

                    kept = 1 if isLastInputKept else 0
                    rewritten = 1 if isLastInputRewritten else 0
                    sumOfRewritten = sumOfRewritten + rewritten
                    sumOfKept = sumOfKept + kept
                    
                                    
            if i >= len(errors):
                errors.append(0)
                rewrittens.append(0)
                kepts.append(0)

            kepts[i] = kepts[i] + sumOfKept/len(TRACES_FILES)
            rewrittens[i] = rewrittens[i] + sumOfRewritten/len(TRACES_FILES)
            errors[i] = errors[i] + abs(sumOfCosts - globalObjective)/len(TRACES_FILES)
            i = i + 1
                
groupBy = 10
j = 0

## (todo) write meaning of values in comment
print (f"#error\trewritten\tkept ({len(errors)})")
for i in range(0, len(errors)):
    if j >= groupBy:
        j = 0
        # print ("{}\t{}".format(counters[i][0], counters[i][1]))
        print (f"{sErrors}\t{sRewrittens}\t{sKepts}")
        
    if j == 0:
        sErrors = 0
        sRewrittens = 0
        sKepts = 0

    sKepts = sKepts + kepts[i]/groupBy
    sErrors = sErrors + errors[i]/groupBy
    sRewrittens = sRewrittens + rewrittens[i]/groupBy
    j = j + 1


