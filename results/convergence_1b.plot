set term postscript eps color blacktext "Helvetica" 24

set output "convergence_1b.eps"
set xrange [0:550]
set yrange [0:1]

plot "convergence.dat" u ($0)*10+5:($1)/8 t "discovering meaningful inputs" w linespoints, \
     "convergence.dat" u ($0)*10+5:($2)/8 t "self-tuning to fit objective" w linespoints
