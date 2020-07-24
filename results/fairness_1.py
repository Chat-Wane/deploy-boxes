import json
import sys
import statistics
import math
from pathlib import Path
from io import BytesIO
from pygnuplot import gnuplot




TRACES_FILES = [Path('result_convergence_3_s11.json'),
                Path('result_convergence_3_s12.json'),
                Path('result_convergence_3_s13.json'),
                Path('result_convergence_3_s14.json'),
                Path('result_convergence_3_s15.json'),]
TRACES_FILES_B = [Path('result_fairness_1_s1.json'),
                  Path('result_fairness_1_s2.json'),
                  Path('result_fairness_1_s3.json'),
                  Path('result_fairness_1_s4.json'),
                  Path('result_fairness_1_s5.json'),]                
TRACES_FILES_C = [Path('result_fairness_2_s1.json'),
                  Path('result_fairness_2_s2.json'),
                  Path('result_fairness_2_s3.json'),
                  Path('result_fairness_2_s4.json'),
                  Path('result_fairness_2_s5.json'),]

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
            


varCosts, errors = getVariancesOf(TRACES_FILES)
print("Done with first set of files")
varCostsB, errorsB = getVariancesOf(TRACES_FILES_B)
print("Done with second set of files")
varCostsC, errorsC = getVariancesOf(TRACES_FILES_C)
print("Done with third set of files")



groupBy = 10
j = 0

with Path(__file__+'.dat').open('w') as f:
    f.write(f"#f=0 var\t err \t f=0.1 var\t err \t f=0.4 var \t err ({len(varCosts)})\n")
    for i in range(0, min([len(varCosts), len(varCostsB),len(varCostsC)])):
        if j >= groupBy:
            f.write(f"{sVarCosts}\t{sumErrors/j}\t{sVarCostsB}\t{sumErrorsB/j}\t{sVarCostsC}\t{sumErrorsC/j}\n")
            j = 0

        if j == 0:
            sVarCosts = 0
            sVarCostsB = 0
            sVarCostsC = 0
            sumVarCosts = 0
            sumVarCostsB = 0
            sumVarCostsC = 0
            sumErrors = 0
            sumErrorsB = 0
            sumErrorsC = 0

        sVarCosts = sVarCosts + varCosts[i] / groupBy
        sVarCostsB = sVarCostsB + varCostsB[i] / groupBy
        sVarCostsC = sVarCostsC + varCostsC[i] / groupBy
        sumVarCosts = sumVarCosts + varCosts[i]
        sumVarCostsB = sumVarCostsB + varCostsB[i]
        sumVarCostsC = sumVarCostsC + varCostsC[i]
        sumErrors = sumErrors + errors[i]
        sumErrorsB = sumErrorsB + errorsB[i]
        sumErrorsC = sumErrorsC + errorsC[i]

        j = j + 1
        
    # if j > 5:
    #     f.write(f"{sumVarCosts/j}\t{sumErrors/j}\t{sumVarCostsB/j}\t{sumErrorsB/j}\t{sumVarCostsC/j}\t{sumErrorsC/j}\n")




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

g.plot(f'"{__file__}.dat" u ($0)*{groupBy}+{groupBy}/2:($2)/1000 t "f=0.0" \
w linespoints lt rgb "orange", \
"{__file__}.dat" u ($0)*{groupBy}+{groupBy}/2:($4)/1000 t "f=0.1" \
w linespoints lt rgb "web-blue", \
"{__file__}.dat" u ($0)*{groupBy}+{groupBy}/2:($6)/1000 t "f=0.4" \
w linespoints lt rgb "forest-green"')

g.cmd('set ylabel "standard deviation"',
      'set yrange [0:650]',
      'set format y "%3.0f"')
g.cmd('set xtics format',
      'set xlabel "#execution"')

g.cmd('set tmargin 0.0',
      'set bmargin')

g.cmd('set key left bottom')

g.plot(f'"{__file__}.dat" u ($0)*{groupBy}+{groupBy}/2:($1) t "f=0.0" \
w linespoints lt rgb "orange", \
"{__file__}.dat" u ($0)*{groupBy}+{groupBy}/2:($3) t "f=0.1" \
 w linespoints lt rgb "web-blue", \
"{__file__}.dat" u ($0)*{groupBy}+{groupBy}/2:($5) t "f=0.4"\
 w linespoints lt rgb "forest-green"')


print (f"Plotted into file {__file__}.eps")
