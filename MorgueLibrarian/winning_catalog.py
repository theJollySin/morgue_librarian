""" Winning Morgue Cataloger
"""
from glob import glob
import os
from sys import argv
from library_data import DATA_DIR, WINNERS


def main():
    """
    1. parse input commandline for winning build/run info
    2. open/read all winning runs in /data/, bzip or not
    3. print lines that match search criteria
    """
    data_dir = DATA_DIR
    winners = WINNERS
    args = ['-', '-', '-', '-', '-']

    for a, arg in enumerate(argv[1:]):
        args[a] = arg

    wc = WinningCatalog(data_dir, winners)
    wc.print_matches(args[0], args[1], args[2], args[3], args[4])


class WinningCatalog:

    def __init__(self, data_dir, prefix):
        self.data_dir = data_dir
        self.prefix = prefix
        self.morgues = {}

    def print_matches(self, species, background, god, num_runes, ver):
        """ TODO
        """
        self.find()

        matches = self.morgues.copy()

        # subset the morgues to match our search criteria
        if species != '-':
            matches = {m:u for m, u in matches.items() if m[0] == species}
        if background != '-':
            matches = {m:u for m, u in matches.items() if m[1] == background}
        if god != '-':
            matches = {m:u for m, u in matches.items() if m[2] == god}
        if num_runes != '-':
            matches = {m:u for m, u in matches.items() if m[3] == int(num_runes)}
        if ver != '-':
            matches = {m:u for m, u in matches.items() if m[4] == float(ver)}

        if not len(matches):
            print('No matches found.')
        else:
            # print all the winning morgues that matches the search criteria
            for build in sorted(matches.keys()):
                b = build[0] + build[1] + '^' + build[2].ljust(4) + str(build[3]).rjust(3) + ' ' + str(build[4]).ljust(5) + '  '
                for line in sorted(matches[build]):
                    print(b + line)

            # TODO: Should be optional
            return

            # print some summary statistics, for the most popular builds that match the search criteria
            build_counts = {}
            for b, us in matches.items():
                build = b[0] + b[1] + '^' + b[2]
                cnt = len(us)
                if build not in build_counts:
                    build_counts[build] = 0
                build_counts[build] += cnt

            max_count = max(build_counts.values())
            print('\nMost popular builds:')
            for build, count in build_counts.items():
                if count >= max_count:
                    print(build)

    def find(self):
        """ TODO

        Returns: None
        """
        # this set of known morgues saves only the hash of the URL or file path, to save space
        self.morgues = {}

        # read any old outputs that are in plain txt format
        old_morgue_files = glob(os.path.join(self.data_dir, self.prefix + '*.txt'))
        for old_file in old_morgue_files:
            with open(old_file, 'r') as f:
                for line in f.readlines():
                    url, build = WinningCatalog.read_winning_line(line)
                    if build not in self.morgues:
                        self.morgues[build]= []
                    self.morgues[build].append(url)

        # read any old outputs that are in bzip2 format
        old_morgue_files = glob(os.path.join(self.data_dir, self.prefix + '*.txt.bz2'))
        for old_file in old_morgue_files:
            with BZ2File(old_file, 'r') as f:
                for line in f.readlines():
                    url, build = WinningCatalog.read_winning_line(line)
                    if build not in self.morgues:
                        self.morgues[build]= []
                    self.morgues[build].append(url)

    @staticmethod
    def read_winning_line(line):
        """ TODO
        """
        url, info = line.strip().split()
        sbg, num_runes, ver = info.split(',')
        if '^' in sbg:
            sb, god = sbg.split('^')
        else:
            sb = sbg
            god = ''
        species = sb[:2]
        background = sb[2:]
        num_runes = int(num_runes)
        ver = float(ver)
        return url, (species, background, god, num_runes, ver)


if __name__ == '__main__':
    main()
