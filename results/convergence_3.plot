set term postscript eps color blacktext "Helvetica" 20
set output "convergence_3.eps"


set multiplot layout 2, 1 spacing 0.5,0.5

set format y "%.1f"

set xrange [0:1200]
set xtics format ""
set grid xtics
set yrange [0:5]

set bmargin 0.45

set ylabel "time (second)"

plot "convergence_3.dat" u ($0)*10+5:($1)/1000 t "error: |objective - cost|" w linespoints lt rgb "orange"

set tmargin 0.45
set bmargin

set xtics format

set xlabel "#execution"
set yrange [0:1]
set key right bottom

set ylabel "metric over |services|"

plot "convergence_3.dat" u ($0)*10+5:($2)/5 t "self-tuning ratio" w linespoints, \
     "convergence_3.dat" u ($0)*10+5:($3)/5 t "local data kept ratio" w linespoints
