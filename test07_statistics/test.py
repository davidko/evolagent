#!/usr/bin/env python

import numpy
import pylab
import random

def test2():
    N = 200
    m = 5
    iterations = 50000
    bins = [0 for _ in range(N)]
    for _ in range(iterations):
        choices = []
        for _ in range(m):
            choices.append(random.randint(0, N-1))
        bins[min(choices)]+=1
    pylab.plot(map(lambda x: float(x)/iterations, bins))
    #pylab.show()

def f(i, N, m):
    numerator = 1
    for j in range (1, m):
        numerator *= (N-i-j)
    return float(numerator)/(N**(m))

def main():
    N = 200
    m = 5
    data = [ f(x, N, m) for x in range(N) ] 
    print(data)
    mysum = numpy.sum(data)
    print(mysum)
    normalized_data = map(lambda x: x/mysum, data)
    print normalized_data
    pylab.plot(normalized_data)
    pylab.show()

if __name__ == '__main__':
    test2()
    main()

