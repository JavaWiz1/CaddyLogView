

import os
import time
import random
import pathlib

def main():
    
    infile = pathlib.Path('./caddy.log')
    outfile = pathlib.Path('./test.log')
    with open(infile, mode='rt') as h_infile:
        with open(outfile, mode='w') as h_outfile:
            lineno = 0
            for line in h_infile:
                lineno += 1
                print(f'line {lineno}')
                h_outfile.write(line)
                h_outfile.flush()
                if lineno > 15:
                    time.sleep(random.randint(1,5))
            time.sleep(5)
            print('EOF')

if __name__ == "__main__":
    main()