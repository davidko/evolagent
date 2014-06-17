#!/usr/bin/env python

import numpy
import pylab
import random

N = 200
m = 1
iterations = 50000

def test3(i, N , m):
    bins = [0 for _ in range(N)]
    for _ in range(iterations):
        i = random.randint(1, N)
        ranks = [x for x in range(0,N)]
        rest = random.sample(ranks, m-1)
        for _ in range(m - i):
            #rand = random.randint(0,
            rest.append(random.randint(0, N-1))
    #pylab.plot(map(lambda x: float(x)/iterations, bins))

def test2():
    bins = [0 for _ in range(N)]
    for _ in range(iterations):
        ranks = [x for x in range(0, N)]
        choices = random.sample(ranks, m)
        bins[min(choices)]+=1
    pylab.plot(map(lambda x: float(x)/iterations, bins))
    #pylab.show()

def choose(n, k):
    if k == 0:
        return 1
    if n == 0:
        return 0
    return choose(n-1, k-1) * n // k

def f2(i, N, m):
    return float(choose(N-i-1, m-1)) / choose(N, m)

def f(i, N, m):
    numerator = 1
    denominator = 1
    k_fac = 1
    for j in range (0, m-1):
        numerator *= (N-i-j)
        denominator *= (N-j)
        k_fac *= j+1
    denominator /= k_fac
    return float(numerator)/denominator

def main():
    """
    data = [ f(x, N, m) for x in range(N) ] 
    print(data)
    mysum = numpy.sum(data)
    print(mysum)
    normalized_data = map(lambda x: x/mysum, data)
    print normalized_data
    pylab.plot(normalized_data)
    """
    data2 = [f2(x, N, m) for x in range(N) ]
    print data2
    pylab.plot(data2)
    pylab.show()

if __name__ == '__main__':
    test2()
    main()

