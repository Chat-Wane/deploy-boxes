import json
import sys
import statistics
import math
from pathlib import Path
from io import BytesIO
from pygnuplot import gnuplot




TRACES_FILES = [[Path('result_convergence_3_s11.json'),
                 Path('result_convergence_3_s12.json'),
                 Path('result_convergence_3_s13.json'),
                 Path('result_convergence_3_s14.json'),
                 Path('result_convergence_3_s15.json'),],
                [Path('result_fairness_1_s1.json'),
                 Path('result_fairness_1_s2.json'),
                 Path('result_fairness_1_s3.json'),
                 Path('result_fairness_1_s4.json'),
                 Path('result_fairness_1_s5.json'),],
                [Path('result_fairness_2_s1.json'),
                 Path('result_fairness_2_s2.json'),
                 Path('result_fairness_2_s3.json'),
                 Path('result_fairness_2_s4.json'),
                 Path('result_fairness_2_s5.json'),]]
PLOT = True



def _getTag(name, tags):
    for tag in tags:
        if (tag['key'] == name):
            return tag['value']
    return None
                                    
def getVariancesOf (traces_files):
    varCosts = []
    errors = []
    for TRACES_FILE in traces_files:
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
            print (f"# traces {len(traces)}")
            for trace in [kv[1] for kv in traces]:
                front = None
                for process in trace['processes']:
                    if (trace['processes'][process]['serviceName'] == 'box-8080'):
                        front = process
                    
                globalObjective = 0            
                sumOfCosts = 0
                costs = []
                for span in trace['spans']:
                    if (span['operationName'] == 'handle'):
                        tags = span['tags']
                        sumOfCosts = sumOfCosts + span['duration'] / 1000
                        if (span['processID'] == front): ## handle@box-8080
                            globalObjective = _getTag('objective', tags)
                        
                        costs.append(span['duration'] / 1000)
                    
                if i >= len(varCosts):
                    varCosts.append(0)
                    errors.append(0)
                
                if len(costs) > 1:
                    varCosts[i] = varCosts[i] + math.sqrt(statistics.variance(costs))/len(traces_files)

                errors[i] = errors[i] + abs(sumOfCosts - globalObjective)/len(traces_files)
                i = i + 1

    return (varCosts, errors)
            


results = []
i = 1
for setOfTraces in TRACES_FILES:
    results.append(getVariancesOf(setOfTraces))
    print (f"Done with set of files {i}…")
    i = i + 1



groupBy = 15
j = 0
groupedResults = [(0, 0) for pair in results]

with Path(__file__+'.dat').open('w') as f:
    f.write(f'#pairs of (variance of costs, error)\n')
    for i in range(0, min([len(pair[0]) for pair in results])):
        if j >= groupBy:
            for pair in groupedResults:
                f.write(f'{pair[0]/j}\t{pair[1]/j}\t')
            f.write('\n')            
            j = 0

        if j == 0:
            groupedResults = [(0, 0) for pair in results]

        for k in range(0, len(results)):
            groupedResults[k] = (groupedResults[k][0] + results[k][0][i],
                                 groupedResults[k][1] + results[k][1][i])
        
        j = j + 1
        
    # if j > 5:
    #     f.write(f"{sumVarCosts/j}\t{sumErrors/j}\t{sumVarCostsB/j}\t{sumErrorsB/j}\t{sumVarCostsC/j}\t{sumErrorsC/j}\t{sumVarCostsD/j}\t{sumErrorsD/j}\n")




if not PLOT:
    print ("No output plot file…")
    sys.exit(0)

g = gnuplot.Gnuplot(log = True,
                    output = f'"{__file__}.eps"',
                    term = 'postscript eps color blacktext "Helvetica" 20',
                    multiplot = 'layout 2, 1 spacing 0.5,0.5')

g.cmd('set xrange [0:1500]',
      'set xtics format ""',)

g.cmd('set ylabel "error (second)"',
      'set format y "%.1f"',
      'set yrange [0:3.5]')

g.cmd('set bmargin 0.75')

g.plot(f'"{__file__}.dat" u ($0)*{groupBy}+{groupBy}/2:($6)/1000 t "f=0.4" \
w linespoint pt 6 lt rgb "forest-green", \
"{__file__}.dat" u ($0)*{groupBy}+{groupBy}/2:($4)/1000 t "f=0.1" \
w linespoint pt 2 lt rgb "web-blue", \
"{__file__}.dat" u ($0)*{groupBy}+{groupBy}/2:($2)/1000 t "f=0.0" \
w linespoint pt 1 lt rgb "orange" \
')


g.cmd('set ylabel "standard deviation (x10^3)"',
      'set yrange [0:1.1]',
      'set format y "%.1f"')
g.cmd('set xtics format',
      'set xlabel "#execution"')

g.cmd('set tmargin 0.0',
      'set bmargin')

g.cmd('set key left bottom')

g.plot(f'"{__file__}.dat" u ($0)*{groupBy}+{groupBy}/2:($1)/1000 t "f=0.0" \
w linespoint lt rgb "orange", \
"{__file__}.dat" u ($0)*{groupBy}+{groupBy}/2:($3)/1000 t "f=0.1" \
 w linespoint lt rgb "web-blue", \
"{__file__}.dat" u ($0)*{groupBy}+{groupBy}/2:($5)/1000 t "f=0.4"\
 w linespoint pt 6 lt rgb "forest-green" \
')



print (f"Plotted into file {__file__}.eps")
