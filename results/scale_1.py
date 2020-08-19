import json
import sys
from pathlib import Path
from io import BytesIO
from pygnuplot import gnuplot



TRACES_FILES = [[Path('result_scale_1_s1.json'),],
                [Path('result_scale_2_s1.json'),],
                [Path('result_scale_3_s1.json'),],
                [Path('result_scale_4_s1.json'),]]

PLOT = True
READ = [False, False, False, False]



def _getTag(name, tags):
    for tag in tags:
        if (tag['key'] == name):
            return tag['value']
    return None

def getKeptsErrorsRewrittens (traces_files):
    kepts = []
    errors = []
    rewrittens = []
    for TRACES_FILE in traces_files:
        if not TRACES_FILE.is_file():
            print ("/!\ The file you try to analyze does not exist.")
            sys.exit(0)
        
        with TRACES_FILE.open('r') as f:
            print ("Loading file…")
            results = json.load(f)
            print ("File loaded…")
        
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

                kepts[i] = kepts[i] + sumOfKept/len(traces_files)/sumOfSpan
                rewrittens[i] = rewrittens[i] + \
                    sumOfRewritten/len(traces_files)/sumOfSpan
                errors[i] = errors[i] + \
                    abs(sumOfCosts - globalObjective)/len(traces_files)
                i = i + 1


    return (kepts, errors, rewrittens)



def readJsonWriteDat (traces_files, i):
    kepts, errors, rewrittens = getKeptsErrorsRewrittens(traces_files)

    groupBy = 10
    j = 0

    with Path(__file__+'_'+str(i)+'.dat').open('w') as f:
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



for shouldRead in range(0, len(READ)):
    if READ[shouldRead] : 
        readJsonWriteDat(TRACES_FILES[shouldRead], shouldRead)
    


if not PLOT:
    print ("No output plot file…")
    sys.exit(0)

g = gnuplot.Gnuplot(log = True,
               output = f'"{__file__}.eps"',
               term = 'postscript eps color blacktext "Helvetica" 20',
               multiplot = 'layout 2, 1 spacing 0.5,0.5')

g.cmd('set ylabel "error (second)"',
      'set format y "%.1f"')
# g.c('set yrange [0:1]')

g.cmd('set xrange [0:1500]',
      'set xtics format ""',
      'set grid xtics')

g.cmd('set bmargin 0.75')

# g.cmd('set arrow 1 from 550,0 to 550,5.5 nohead dt "." lc "black"',
#       'set arrow 2 from 650,0 to 650,5.5 nohead dt "." lc "black"')

g.plot(f'\
"{__file__}_0.dat" u ($0)*10+5:($1)/1000 t "127 services" w linespoints lt rgb "orange", \
"{__file__}_1.dat" u ($0)*10+5:($1)/1000 t "63 services" w linespoints lt rgb "web-blue", \
"{__file__}_2.dat" u ($0)*10+5:($1)/1000 t "31 services" w linespoints lt rgb "forest-green", \
"{__file__}_3.dat" u ($0)*10+5:($1)/1000 t "15 services" w linespoints lt rgb "purple" \
')

g.cmd('set tmargin 0.0',
      'set bmargin')

g.cmd('set xtics format',
      'set xlabel "#execution"')

g.cmd('set ylabel "metric over |services|"',
      'set yrange [0:1]',
      'set format y "  %.1f"')

g.cmd('set key right center')

# g.cmd('set arrow 1 from 550,0 to 550,1',
#       'set arrow 2 from 650,0 to 650,1')
# g.cmd('set arrow from 550,0.35 to 650,0.35 heads',
g.cmd('set label at 1475,0.9 right "self-tuning ratio"',
      'set label at 1475,0.1 right "local data kept ratio"')


g.plot(f'\
"{__file__}_0.dat" u ($0)*10+5:($2) t "127 services" w linespoints lt rgb "orange",\
"{__file__}_0.dat" u ($0)*10+5:($3) notitle w linespoints pt 1 lt rgb "orange",\
"{__file__}_1.dat" u ($0)*10+5:($2) t "63 services" w linespoints pt 2 lt rgb "web-blue",\
"{__file__}_1.dat" u ($0)*10+5:($3) notitle w linespoints pt 2 lt rgb "web-blue",\
"{__file__}_2.dat" u ($0)*10+5:($2) t "31 services" w linespoints pt 3 lt rgb "forest-green",\
"{__file__}_2.dat" u ($0)*10+5:($3) notitle w linespoints pt 3 lt rgb "forest-green",\
"{__file__}_3.dat" u ($0)*10+5:($2) t "15 services" w linespoints pt 4 lt rgb "purple", \
"{__file__}_3.dat" u ($0)*10+5:($3) notitle w linespoints pt 4 lt rgb "purple" \
')

print (f"Plotted into file {__file__}.eps")
