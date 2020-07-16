set term postscript eps color blacktext "Helvetica" 20
set output "failures_1.eps"


set multiplot layout 2, 1 spacing 0.5,0.5

set format y "%.1f"

set xrange [0:1200]
set xtics format ""
# set grid xtics
set yrange [0:5]

set bmargin 0.75

set ylabel "time (second)"

set arrow 1 from 550,0 to 550,5 nohead dt "." lc "black"
set arrow 2 from 650,0 to 650,5 nohead dt "." lc "black"

plot "failures_1.dat" u ($0)*10+5:($1)/1000 t "error: |objective - cost|" w linespoints lt rgb "orange"

set tmargin 0.0
set bmargin

set xtics format

set xlabel "#execution"
set yrange [0:1]
set key right bottom

set ylabel "metric over |services|"

set arrow 1 from 550,0 to 550,1
set arrow 2 from 650,0 to 650,1
set arrow from 550,0.35 to 650,0.35 heads
set label at 600,0.42 center "-1 service"


plot "failures_1.dat" u ($0)*10+5:($2) t "self-tuning ratio" w linespoints, \
     "failures_1.dat" u ($0)*10+5:($3) t "local data kept ratio" w linespoints
