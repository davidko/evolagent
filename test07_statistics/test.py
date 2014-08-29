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

def sim_selection(N, m, iterations):
    bins = [0 for _ in range(N)]
    for _ in range(iterations):
        ranks = [x for x in range(0, N)]
        choices = random.sample(ranks, m)
        bins[min(choices)]+=1
    return map(lambda x: float(x)/iterations, bins)

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

def R2(data, estdata):
    sse = 0
    for i in range(len(estdata)):
        sse += (estdata[i]-data[i])**2
    sst = 0
    mean = numpy.mean(data)
    for i in range(len(estdata)):
        sst += (data[i] - mean)**2
    return 1-(sse/sst)

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
    """
    data2 = [f2(x, N, m) for x in range(N) ]
    print data2
    pylab.plot(data2)
    pylab.show()
    """
    fig = pylab.figure(1, figsize=(8,5))
    subfig = fig.add_subplot(111)

    eqdata1 = [f2(x, 200, 2) for x in range(200)]
    data1 = sim_selection(200, 2, 50000)
    r2 = R2(data1, eqdata1)
    print('R**2 is {0}'.format(r2))
    subfig.plot(eqdata1, 'r', label='Best of 2')
    subfig.plot(data1, 'r.', alpha=0.25)
    subfig.annotate('R^2 = {0}'.format(r2), 
        xy = (10, eqdata1[10]), 
        xytext = (50, 0.02),
        arrowprops = dict(
            arrowstyle="->", 
            connectionstyle="angle3,angleA=180,angleB=45"))


    eqdata2 = [f2(x, 200, 3) for x in range(200)]
    data2 = sim_selection(200, 3, 50000)
    r2 = R2(data2, eqdata2)
    print('R**2 is {0}'.format(r2))
    subfig.plot(eqdata2, 'g--', label='Best of 3')
    subfig.plot(data2, 'g.', alpha=0.25)
    subfig.annotate('R^2 = {0}'.format(r2), 
        xy = (10, eqdata2[10]), 
        xytext = (50, 0.03),
        arrowprops = dict(
            arrowstyle="->", 
            connectionstyle="angle3,angleA=180,angleB=45"))

    eqdata3 = [f2(x, 200, 10) for x in range(200)]
    data3 = sim_selection(200, 10, 50000)
    r2 = R2(data2, eqdata2)
    print('R**2 is {0}'.format(r2))
    subfig.plot(eqdata3, 'b-.', label='Best of 10')
    subfig.plot(data3, 'b.', alpha=0.25)
    subfig.annotate('R^2 = {0}'.format(r2), 
        xy = (10, eqdata3[10]), 
        xytext = (50, 0.04),
        arrowprops = dict(
            arrowstyle="->", 
            connectionstyle="angle3,angleA=180,angleB=45"))

    pylab.xlabel("Ranked population members (Lower rank = higher fitness)")
    pylab.ylabel("Probability of selection")
    
    pylab.legend()
    pylab.show()

if __name__ == '__main__':
    main()

