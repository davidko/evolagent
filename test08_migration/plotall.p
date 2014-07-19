#set ytics 10 nomirror tc lt 1
set ylabel 'Population Fitness' tc lt 1
#set y2tics 20 nomirror tc lt 2
set y2tics
set y2label 'Genepool Diversity' tc lt 3
plot 'plotdata.dat' using 2:4 with lines title 'Avg Fitness', \
     'plotdata.dat' using 2:5 with lines title 'Max Fitness', \
     'plotdata.dat' using 2:6 with lines axes x1y2 title 'Diversity'
