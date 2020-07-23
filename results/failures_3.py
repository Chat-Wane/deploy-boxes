import json
import sys
from pathlib import Path
from io import BytesIO
from pygnuplot import gnuplot



TRACES_FILES = [Path('result_failures_3_s1.json'),
                Path('result_failures_3_s2.json'),
                Path('result_failures_3_s3.json'),
                Path('result_failures_3_s4.json'),
                Path('result_failures_3_s5.json'),]
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
      'set xtics format ""')

g.cmd('set bmargin 0.75')

g.cmd('set arrow 1 from 200,0 to 200,3.5 nohead dt "." lc "black"',
      'set arrow 2 from 300,0 to 300,3.5 nohead dt "." lc "black"')
g.cmd('set arrow 3 from 700,0 to 700,3.5 nohead dt "." lc "black"',
      'set arrow 4 from 800,0 to 800,3.5 nohead dt "." lc "black"')
g.cmd('set arrow 5 from 1200,0 to 1200,3.5 nohead dt "." lc "black"',
      'set arrow 6 from 1300,0 to 1300,3.5 nohead dt "." lc "black"')
g.cmd('set arrow from 200,2.5 to 300,2.5 heads',
      'set label at 250,2.67 center "-3 services"')
g.cmd('set arrow from 700,2.5 to 800,2.5 heads',
      'set label at 750,2.67 center "-2 services"')
g.cmd('set arrow from 1200,2.5 to 1300,2.5 heads',
      'set label at 1250,2.67 center "-1 service"')

g.plot(f'"{__file__}.dat" u ($0)*10+5:($1)/1000 t "error: |objective - cost|" w linespoints lt rgb "orange"')

g.cmd('set tmargin 0.0',
      'set bmargin')

g.cmd('set xtics format',
      'set xlabel "#execution"')

g.cmd('set ylabel "metric over |services|"',
      'set yrange [0:1]')

g.cmd('set key center right')

g.cmd('set arrow 1 from 200,0 to 200,1 nohead dt "." lc "black"',
      'set arrow 2 from 300,0 to 300,1 nohead dt "." lc "black"')
g.cmd('set arrow 3 from 700,0 to 700,1 nohead dt "." lc "black"',
      'set arrow 4 from 800,0 to 800,1 nohead dt "." lc "black"')
g.cmd('set arrow 5 from 1200,0 to 1200,1 nohead dt "." lc "black"',
      'set arrow 6 from 1300,0 to 1300,1 nohead dt "." lc "black"')

g.plot(f'"{__file__}.dat" u ($0)*10+5:($2) t "self-tuning ratio" w linespoints,\
"{__file__}.dat" u ($0)*10+5:($3) t "local data kept ratio" w linespoints')

print (f"Plotted into file {__file__}.eps")
