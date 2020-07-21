import json
import sys
from pathlib import Path
from io import BytesIO
from pygnuplot import gnuplot



TRACES_FILES = [Path('result_convergence_3_s11.json'),
                Path('result_convergence_3_s12.json'),
                Path('result_convergence_3_s13.json'),
                Path('result_convergence_3_s14.json'),
                Path('result_convergence_3_s15.json'),
                Path('result_convergence_3_s16.json'),]
PLOT = True



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
            sumOfSpan = 0
            for span in trace['spans']:
                if (span['operationName'] == 'handle'):
                    sumOfSpan = 1 + sumOfSpan
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

            kepts[i] = kepts[i] + sumOfKept/len(TRACES_FILES)/sumOfSpan
            rewrittens[i] = rewrittens[i] + sumOfRewritten/len(TRACES_FILES)/sumOfSpan
            errors[i] = errors[i] + abs(sumOfCosts - globalObjective)/len(TRACES_FILES)
            i = i + 1
            

            
groupBy = 10
j = 0

with Path(__file__+'.dat').open('w') as f:
    f.write(f"#error\trewritten\tkept ({len(errors)})\n")
    for i in range(0, len(errors)):
        if j >= groupBy:
            j = 0
            # print ("{}\t{}".format(counters[i][0], counters[i][1]))
            f.write(f"{sErrors}\t{sRewrittens}\t{sKepts}\n")
        
        if j == 0:
            sErrors = 0
            sRewrittens = 0
            sKepts = 0

        sKepts = sKepts + kepts[i]/groupBy
        sErrors = sErrors + errors[i]/groupBy
        sRewrittens = sRewrittens + rewrittens[i]/groupBy
        j = j + 1



if not PLOT:
    print ("No output plot file…")
    sys.exit(0)

g = gnuplot.Gnuplot(log = True,
               output = f'"{__file__}.eps"',
               term = 'postscript eps color blacktext "Helvetica" 20',
               multiplot = 'layout 2, 1 spacing 0.5,0.5')

g.cmd('set ylabel "time (second)"',
      'set format y "%.1f"')
# g.c('set yrange [0:1]')

g.cmd('set xrange [0:1500]',
      'set xtics format ""',
      'set grid xtics')

g.cmd('set bmargin 0.75')

# g.cmd('set arrow 1 from 550,0 to 550,5.5 nohead dt "." lc "black"',
#       'set arrow 2 from 650,0 to 650,5.5 nohead dt "." lc "black"')

g.plot(f'"{__file__}.dat" u ($0)*10+5:($1)/1000 t "error: |objective - cost|" w linespoints lt rgb "orange"')

g.cmd('set tmargin 0.0',
      'set bmargin')

g.cmd('set xtics format',
      'set xlabel "#execution"')

g.cmd('set ylabel "metric over |services|"',
      'set yrange [0:1]')

g.cmd('set key right bottom')

# g.cmd('set arrow 1 from 550,0 to 550,1',
#       'set arrow 2 from 650,0 to 650,1')
# g.cmd('set arrow from 550,0.35 to 650,0.35 heads',
#       'set label at 600,0.42 center "-1 service"')


g.plot(f'"{__file__}.dat" u ($0)*10+5:($2) t "self-tuning ratio" w linespoints,\
"{__file__}.dat" u ($0)*10+5:($3) t "local data kept ratio" w linespoints')

print (f"Plotted into file {__file__}.eps")
