import json
import sys
from pathlib import Path
from io import BytesIO



TRACES_FILES = [Path('result_convergence_1b_s1.json'),            
                Path('result_convergence_1b_s2.json'),
                Path('result_convergence_1b_s3.json'),
                Path('result_convergence_1b_s4.json'),
                Path('result_convergence_1b_s5.json'),
                Path('result_convergence_1b_s6.json'),
                Path('result_convergence_1b_s7.json'),
                Path('result_convergence_1b_s8.json')]




counters = []

for TRACES_FILE in TRACES_FILES:
    if not TRACES_FILE.is_file():
        print ("/!\ The file you try to analyze does not exist.")
        sys.exit(0)

    with TRACES_FILE.open('r') as f:
        results = json.load(f)

        changes = []
        rewritten = []
        for trace in results['data']:
            for span in trace['spans']:
                if (span['operationName'] == 'handle'):
                    start = span['startTime']
                    hasTagRewritten = False
                    for tag in span['tags']:
                        if (tag['key'] == 'isLastInputKept'):
                            changes.append((start, tag['value']))
                        if (tag['key'] == 'isLastInputRewritten'):
                            hasTagRewritten = True
                            rewritten.append((start, tag['value']))
                    if not hasTagRewritten:
                        rewritten.append(start, False)
                
        changes = sorted(changes, key=lambda x: x[0])
        rewritten = sorted(rewritten, key=lambda x: x[0])

        for i in range(0, len(changes)):
            if (i >= len(counters)):
                counters.append((0, 0))
        
            left = 1 if changes[i][1] else 0;
            right = 1 if rewritten[i][1] else 0;

            counters[i] = (counters[i][0] + left, counters[i][1] + right)

groupBy = 10
j = 0
for i in range(0, len(counters)):
    if j >= groupBy:
        j = 0
        # print ("{}\t{}".format(counters[i][0], counters[i][1]))
        print ("{}\t{}".format(s[0], s[1]))
        
    if j == 0:
        s = (0, 0)
        
    s = (s[0] + counters[i][0]/groupBy, s[1] + counters[i][1]/groupBy)
    j = j + 1


