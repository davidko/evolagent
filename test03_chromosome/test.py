#!/usr/bin/env python

import random
import tempfile
import subprocess
import math

from evolagent import Chromosome

class GaitChromosome(Chromosome):
    def fitness_function(self):
        # First, save fitness to a temporary file
        f = tempfile.NamedTemporaryFile()
        f.write(str(self).encode('utf-8'))
        command = [ 'gait_fitness',  
                    '--disable-graphics',  
                    '--load-coefs', '{}'.format(f.name)]
        print(command)
        output = subprocess.check_output(command)
        positions = output.split()
        distance = 0.0;
        for p in positions:
          distance = distance + float(p)**2
        distance = math.sqrt(distance)
        print(distance)
        self.__fitness = distance
        f.close()
        return distance

    def crossover(self, other):
        if len(self.genes) != len(other.genes):
            raise EvolError('Gene lengths do not match.')
        cutpoint = random.randint(1, len(self.genes)-1)
        # Use a random number to determine whose genes go first during
        # crossover
        new_chro = None
        if random.randint(0, 1):
            new_chro = self.genes[0:cutpoint] + other.genes[cutpoint:]
        else:
            new_chro = other.genes[0:cutpoint] + self.genes[cutpoint:]
        return GaitChromosome(new_chro)

def main():
    numtests = 20
    numgenes = 120
    for _ in range(numtests):
        c1 = GaitChromosome([random.randint(0, 255) for _ in range(120)])
        c2 = GaitChromosome([random.randint(0, 255) for _ in range(120)])
        c3 = c1.crossover(c2)
        assert(len(c3.genes) == len(c2.genes))
        print('{0} {1} {2}'.format(
            c1.fitness_function(), c2.fitness_function(),
            c3.fitness_function()))

if __name__=="__main__":
    main()
