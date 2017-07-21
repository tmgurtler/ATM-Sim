# Python code that calculates statistics on data collected

import matplotlib
from scipy import stats
from collections import defaultdict
from dateutil import parser
from matplotlib.ticker import FuncFormatter
from contextlib import contextmanager
import sys
import matplotlib.pyplot as plt
import matplotlib.mlab as mlab
import numpy as np
import itertools
import math
import sqlite3
import os

CODE_FOR_BACKSPACE = "b"
CODE_FOR_ENTER = "e"

# defined (and so large) mostly just for convenience's sake
all_sets = {
    "dist_zero": ["00", "11", "22", "33", "44", "55", "66", "77", "88", "99"],
    "dist_one": ["12", "23", "45", "56", "78", "89", "21", "32", "54", "65", "87", "98", "14", "47", "25", "58", "36", "69", "41", "74", "52", "85", "63", "96", "80", "08"],
    "dist_one_horizontal": ["12", "23", "45", "56", "78", "89", "21", "32", "54", "65", "87", "98"],
    "dist_one_left": ["21", "32", "54", "65", "87", "98"],
    "dist_one_right": ["12", "23", "45", "56", "78", "89"],
    "dist_one_vertical": ["14", "47", "25", "58", "36", "69", "41", "74", "52", "85", "63", "96", "80", "08"],
    "dist_one_up": ["41", "74", "52", "85", "63", "96", "08"],
    "dist_one_down": ["14", "47", "25", "58", "36", "69", "80"],
    "dist_two": ["13", "46", "79", "31", "64", "97", "17", "28", "39", "71", "82", "93", "50", "05"],
    "dist_two_horizontal": ["13", "46", "79", "31", "64", "97"],
    "dist_two_left": ["31", "64", "97"],
    "dist_two_right": ["13", "46", "79"],
    "dist_two_vertical": ["17", "28", "39", "71", "82", "93", "50", "05"],
    "dist_two_up": ["71", "82", "93", "05"],
    "dist_two_down": ["17", "28", "39", "50"],
    "dist_three": ["20", "02"],
    "dist_three_up": ["02"],
    "dist_three_down": ["20"],
    "dist_diagonal_one": ["15", "26", "24", "35", "48", "59", "57", "68", "70", "90", "51", "62", "42", "53", "84", "95", "75", "86", "07", "09"],
    "dist_diagonal_two": ["19", "37", "91", "73"],
    "dist_dogleg": ["16", "18", "27", "29", "34", "38", "43", "49", "40", "61", "67", "60", "72", "76", "81", "83", "92", "94", "04", "06"],
    "dist_long_dogleg": ["10", "30", "01", "03"],
    "zero_to_enter": ["0e"],
    "one_to_enter": ["1e"],
    "two_to_enter": ["2e"],
    "three_to_enter": ["3e"],
    "four_to_enter": ["4e"],
    "five_to_enter": ["5e"],
    "six_to_enter": ["6e"],
    "seven_to_enter": ["7e"],
    "eight_to_enter": ["8e"],
    "nine_to_enter": ["9e"]
}

# all the different distance one sets (varying direction)
dir_one_sets = [
    "dist_one",
    "dist_one_horizontal",
    "dist_one_vertical",
    "dist_one_up",
    "dist_one_right",
    "dist_one_down",
    "dist_one_left"
]

# all the different distance two sets (varying direction)
dir_two_sets = [
    "dist_two",
    "dist_two_horizontal",
    "dist_two_vertical",
    "dist_two_up",
    "dist_two_right",
    "dist_two_down",
    "dist_two_left"
]

# all the different distance three sets (varying direction)
dir_three_sets = [
    "dist_three",
    "dist_three_up",
    "dist_three_down"
]

# all the sets from a number to enter
to_enter_sets = [
    "zero_to_enter",
    "one_to_enter",
    "two_to_enter",
    "three_to_enter",
    "four_to_enter",
    "five_to_enter",
    "six_to_enter",
    "seven_to_enter",
    "eight_to_enter",
    "nine_to_enter"
]

# compare zero to enter against distance two (same distance, theoretically)
enter_checker_zero_sets = [
    "zero_to_enter",
    "dist_two"
]

# compare long distances to enter (similar)
enter_checker_one_sets = [
    "one_to_enter",
    "two_to_enter",
    "four_to_enter"
]

# compare the long doglegs vs. numbers to enter (same distance, theoretically)
enter_checker_three_sets = [
    "three_to_enter",
    "seven_to_enter",
    "dist_long_dogleg"
]

# compare the diagonal two distance vs. five to enter (same distance, theoretically)
enter_checker_five_sets = [
    "five_to_enter",
    "dist_diagonal_two"
]

# compare the doglegs vs. numbers to enter (same distance, theoretically)
enter_checker_six_sets = [
    "six_to_enter",
    "eight_to_enter",
    "dist_dogleg"
]

# compare the diagonal one distance vs. nine to enter (same distance, theoretically)
enter_checker_nine_sets = [
    "nine_to_enter",
    "dist_diagonal_one"
]

# compare just the straight line distances
mainline_dist_sets = [
    "dist_zero",
    "dist_one",
    "dist_two",
    "dist_three"
]

# compare the distances between one and two, inclusive
betweener_one_sets = [
    "dist_one",
    "dist_diagonal_one",
    "dist_dogleg",
    "dist_two"
]

# compare the distances between two and three, inclusive
betweener_two_sets = [
    "dist_two",
    "dist_diagonal_two",
    "dist_long_dogleg",
    "dist_three"
]

# compare all the distances
dist_sets = [
    "dist_zero",
    "dist_one",
    "dist_two",
    "dist_three",
    "dist_diagonal_one",
    "dist_diagonal_two",
    "dist_dogleg",
    "dist_long_dogleg"
]

##
# This functionality allows us to temporarily change our working directory
#
# @input newdir - the new directory (relative to our current position) we want to be in
@contextmanager
def cd(newdir):
    prevdir = os.getcwd()
    os.chdir(os.path.expanduser(newdir))
    try:
        yield
    finally:
        os.chdir(prevdir)

##
# This functionality allows us to temporarily change where stdout routes
#
# @input new_out - the file that stdout will get routed to temporarily
@contextmanager
def change_stdout(new_out):
    prev_out = sys.stdout
    sys.stdout = open(new_out, 'w')
    try:
        yield
    finally:
        sys.stdout.close()
        sys.stdout = prev_out

##
# This function pulls data from the SQLite database
#
# @returns a list of 4-tuples of keystroke timings
def retrieve_data():
    conn = sqlite3.connect('attempts.db')
    c = conn.cursor()

    c.execute('SELECT userString, pinAttempted, keyPressed, time FROM attempts')
    res = c.fetchall()
    conn.close()

    return res

##
# This function organizes data by user and PIN
#
# @input res - a list of 4-tuples of keystroke timings
# @returns a dictionary of dictionaries of pairs,
#           where the top-level dictionary connects users to all PINs they enter and
#           the lower dictionary connects a PIN to all keystrokes used while entering the PIN and timings of each
#           in the format of a list of pairs (key pressed, time)
def preprocess_data(res):
    keystrokes = defaultdict(lambda: defaultdict(lambda: []))

    # make sure data is sorted by timestamp
    res = sorted(res, key=lambda x: x[3])

    # parser.parse reads a timestamp into a Python timedate object
    for keystroke in res:
        keystrokes[keystroke[0]][int(keystroke[1])].append((keystroke[2], parser.parse(keystroke[3])))

    return keystrokes

##
# This function organizes data by individual PIN attempt,
# while throwing out attempts that include using the clear button or are just incorrect
#
# @input keystrokes - a dictionary of dictionaries of lists of pairs of keystrokes and timings
# @returns a dictionary of dictionaries of lists of lists of pairs,
#           where the top-level dictionary connects users to all PINs they enter and
#           the lower dictionary connects a PIN to all keystrokes used while entering the PIN and timings of each
#           in the format of a list of lists of pairs [[data corresponding to entering one PIN once] ... [(key pressed, time) ...] ...]
def clean_data(keystrokes):
    for user, user_data in keystrokes.items():
        for pin, pin_data in user_data.items():
            # collector for each sublist, which correspond to individual PINs
            all_attempts = []

            attempt = []
            flag_backspace = False
            
            for (key, time) in pin_data:
                # throw out any attempt that involves a backspace
                if key == CODE_FOR_BACKSPACE:
                    flag_backspace = True

                # enter is the last key pressed per PIN entry
                if key != CODE_FOR_ENTER:
                    attempt.append((key, time))
                else:
                    # default to assuming the PIN is wrong
                    flag_incorrect = True
                    # needs try/except because some entries are "" and int("") throws an exception
                    try:
                        pin_entered = int("".join([x for (x,y) in attempt]))
                        flag_incorrect = pin_entered != pin
                    except:
                        pass

                    # don't leave out the enter keystroke
                    attempt.append((key, time))

                    # only add our PIN attempt if it is good
                    if not flag_backspace and not flag_incorrect:
                        all_attempts.append(attempt)
                    
                    # only reset things at new PIN
                    attempt = []
                    flag_backspace = False

            keystrokes[user][pin] = all_attempts

    return keystrokes

##
# This function parses keystroke data into interkey timing data
#
# @input keystrokes - a dictionary of dictionaries of lists of lists of pairs of keystrokes and timings
# @returns a dictionary of ints,
#           where the dictionary connects a keypair (e.g. "12")
#           to every interkey timing used to enter it
def parse_data(keystrokes):
    all_timings = defaultdict(lambda: [])

    for user, user_data in keystrokes.items():
        for pin, pin_data in user_data.items():
            entry_bigrams = []

            # collect every bigram from all attempts
            for attempt in pin_data:
                entry_bigrams.extend([(key_a + key_b, times_b - times_a) for ((key_a, times_a), (key_b, times_b)) in zip(attempt[:-1], attempt[1:])])

            # put bigrams in the dictionary and convert Python timedelta objects to integers
            for (bigram, time_diff) in entry_bigrams:
                time_diff_in_ms = int(math.floor(((time_diff.seconds * (10**6)) + time_diff.microseconds) / (10**3)))
                all_timings[bigram].append(time_diff_in_ms)

    return all_timings

##
# This function parses keystroke data into interkey timing data while separating data by user
#
# @input keystrokes - a dictionary of dictionaries of lists of lists of pairs of keystrokes and timings
# @returns a list of dictionaries of ints,
#           where the dictionaries connect keypairs (e.g. "12")
#           to every interkey timing used to enter it by a given user
def parse_data_per_user(keystrokes):
    collector = []

    for user, user_data in keystrokes.items():
        all_timings = defaultdict(lambda: [])
        for pin, pin_data in user_data.items():
            entry_bigrams = []

            # collect every bigram from all attempts
            for attempt in pin_data:
                entry_bigrams.extend([(key_a + key_b, times_b - times_a) for ((key_a, times_a), (key_b, times_b)) in zip(attempt[:-1], attempt[1:])])

            # put bigrams in the dictionary and convert Python timedelta objects to integers
            for (bigram, time_diff) in entry_bigrams:
                time_diff_in_ms = int(math.floor(((time_diff.seconds * (10**6)) + time_diff.microseconds) / (10**3)))
                all_timings[bigram].append(time_diff_in_ms)
        collector.append(all_timings)

    return collector

##
# This function roots out the highest X% of data as outliers
#
# @input timings - a dictionary of lists of ints, where the dictionary
#                   connects a keypair (e.g. "12") to every interkey
#                   timing used to enter it
# @input percentile - the threshold above which data gets thrown out
#                       (defaults to 95th, as in top 5% gets thrown out)
# @returns a dictionary of lists of ints,
#           where the dictionary connects keypairs (e.g. "12")
#           to every interkey timing used to enter it (without outliers)
def filter_timings(timings, percentile=95):
    # get just the timings to figure out percentiles on them
    just_the_timings = [timing for bigram, set_of_timings in timings.items() for timing in set_of_timings]
    bar = np.percentile(just_the_timings, percentile)

    # filter out all timings which fall below the threshold
    good_pairs = [(bigram, list(filter(lambda x: x < bar, timing))) for bigram, timing in timings.items()]
    ret = defaultdict(lambda: [])

    # put our new timings back together in the dictionary
    for (bigram, timing) in good_pairs:
        ret[bigram] = (timing)

    return ret

##
# This function roots out the highest X% of data as outliers, while keeping data separate per user
#
# @input timings - a list of dictionaries of lists of ints, where the dictionaries
#                   connect keypairs (e.g. "12") to every interkey
#                   timing used to enter it by a single user
# @input percentile - the threshold above which data gets thrown out
#                       (defaults to 95th, as in top 5% gets thrown out)
# @returns a list of dictionaries of lists of ints,
#           where the dictionaries connect keypairs (e.g. "12")
#           to every interkey timing used by a single user to enter it (without outliers)
def filter_timings_per_user(timings, percentile=95):
    ret = []

    for user_data in timings:
        # get just the timings to figure out percentiles on them
        just_the_timings = [timing for bigram, set_of_timings in user_data.items() for timing in set_of_timings]
        bar = np.percentile(just_the_timings, percentile)

        # filter out all timings which fall below the threshold
        good_pairs = [(bigram, list(filter(lambda x: x < bar, timing))) for bigram, timing in user_data.items()]
        curr = defaultdict(lambda: [])

        # put our new timings back together in the dictionary
        for (bigram, timing) in good_pairs:
            curr[bigram] = (timing)
        ret.append(curr)

    return ret


##
# This function combines all functionalities pertaining obtaining and cleaning data
#
# @returns a dictionary of ints,
#           where the dictionary connects a keypair (e.g. "12")
#           to every interkey timing used to enter it
def obtain_timings():
    raw_data = retrieve_data()
    keystrokes = preprocess_data(raw_data)
    keystrokes = clean_data(keystrokes)
    timings = parse_data(keystrokes)

    return timings

##
# This function combines all functionalities pertaining obtaining and cleaning data, but on a per user level
#
# @returns a dictionary of ints,
#           where the dictionary connects a keypair (e.g. "12")
#           to every interkey timing used to enter it
def obtain_timings_per_user():
    raw_data = retrieve_data()
    keystrokes = preprocess_data(raw_data)
    keystrokes = clean_data(keystrokes)
    timings = parse_data_per_user(keystrokes)

    return timings


##
# This function tests whether the keypairs within a given set have significantly different timings from one another
#
# @input timings - a dictionary of keypairs with their timings
# @input given_set - what set of keypairs to test
def relevance_within_set(timings, given_set, name_of_set, user):
    print "P-value within " + name_of_set + " for user " + user
    print "---"

    # only test the keypairs we actually have data for
    active_set = [x for x in given_set if x in timings.keys()]
    test_pairs = itertools.combinations(active_set, 2)
    
    for x, y in test_pairs:
        t_statistic, p_value = stats.ttest_ind(timings[x], timings[y], equal_var=False)
        print "keypair 1: %s\nkeypair 2: %s\nt: %f\np value: %f\n" % (x, y, t_statistic, p_value)
    print ""

##
# This function only serves to make things look prettier for the histograms
def to_percent(y, position):
    # Ignore the passed in position. This has the effect of scaling the default
    # tick locations.
    s = str(100 * y)

    # The percent symbol needs escaping in latex
    if matplotlib.rcParams['text.usetex'] is True:
        return s + r'$\%$'
    else:
        return s + '%'

##
# This function finds the mean and standard deviation of a given set and outputs
# those statistics
#
# @input timings - the set of all timings
# @input given_set - the set to find the mean and standard deviations
# @input name_of_set - a string denoting the name of the set
# @input user - a string identifying the user
def mean_std_of_set(timings, given_set, name_of_set, user):
    print "Mean and STD of " + name_of_set + " for user " + user
    print "---"

    # only test the keypairs we actually have data for
    active_set = [timings[x] for x in given_set]
    active_set = [item for sublist in active_set for item in sublist]
    
    std = np.std(active_set)
    mean = np.mean(active_set)

    print "mean: %f\nstandard deviation: %f\n" % (mean, std)

##
# This function produces a histogram for a given set
#
# @input timings - the set of all timings
# @input given_set - the set to produce a histogram for
# @input name_of_set - a string denoting the name of the set
# @input user - a string identifying the user
def hist_of_set(timings, given_set, name_of_set):
    with cd('plots'):
        # only test the keypairs we actually have data for
        active_set = [timings[x] for x in given_set]
        active_set = [item for sublist in active_set for item in sublist]
        num = len(active_set)

        # if no data, don't bother plotting anything
        if not bool(active_set):
            return

        # Fit a gamma distribution to the data observed

        # alpha, loc, beta = stats.gamma.fit(active_set)
        # scale = beta ** (-1)
        # x = np.linspace(0, 650, 1000)
        # model_name = name_of_set +"\nmodeled as Gamma dist"

        ##
        # this is a hack so that we can always make sure that
        # the same class gets the same color, independent of run

        # color = {
        #     "dist_zero": "black",
        #     "dist_one": "red",
        #     "dist_two": "blue",
        #     "dist_three": "green",
        #     "dist_diagonal_one": "magenta",
        #     "dist_dogleg": "orange",
        #     "dist_long_dogleg": "cyan",
        #     "dist_diagonal_two": "purple"
        # }

        # plot the gamma distribution model of the data
        # plt.plot(x,stats.gamma.pdf(x, alpha, loc=loc, scale=beta),'--', color=color[name_of_set],label=model_name)

        # force the histogram bin edges to always fall on multiples of 25, from 50 to 625
        bin_setter = [50, 75, 100, 125, 150, 175, 200, 225, 250, 275, 300, 325, 350, 375, 400, 425, 450, 475, 500, 525, 550, 575, 600, 625]
        ys, binEdges = np.histogram(active_set, bins=bin_setter, normed=True)

        ##
        # xs should be the middle of the bin
        # (and using binEdges for this means that we can guarantee len(xs) == len(ys))
        xs = [(x + y) / 2 for x, y in zip(binEdges[:-1], binEdges[1:])]
        name = name_of_set + "\nn = " + str(num)

        # here we plot a rough fit to the histogram, so that multiple overlapping distributions can be seen at once
        plt.plot(xs, ys,'-',label=name)
    
##
# This function tests whether two given sets have significantly different timings from one another
#
# @input timings - a dictionary of keypairs with their timings
# @input set_a - the first set of keypairs to test
# @input set_b - the first set of keypairs to test
def relevance_between_sets(timings, set_a, name_a, set_b, name_b):
    # collect all timings from all keypairs in the sets
    timings_for_a = [timings[x] for x in set_a]
    timings_for_a = [item for sublist in timings_for_a for item in sublist]

    timings_for_b = [timings[x] for x in set_b]
    timings_for_b = [item for sublist in timings_for_b for item in sublist]

    t_statistic, p_value = stats.ttest_ind(timings_for_a, timings_for_b, equal_var=False)
    print "%s vs. %s\nt: %f\np value: %f\n" % (name_a, name_b, t_statistic, p_value)

##
# This function compares every combination of two sets within a superset,
# to see if they have significantly different timings from one another
#
# @input timings - a dictionary of keypairs with their timings
# @input set_a - the first set of keypairs to test
# @input set_b - the first set of keypairs to test
def relevance_between_sets_from_superset(timings, superset):
    for name_a, name_b in itertools.combinations(superset, 2):
        relevance_between_sets(timings, all_sets[name_a], name_a, all_sets[name_b], name_b)

##
# Perform all functionality with data from all users
def main_all():
    timings = obtain_timings()
    timings = filter_timings(timings)

    with cd('outputs'):
        with change_stdout('all_users.out'):
            print "Analyzing all users:\n"
            print "~~~~~~~~~~~~~~~~~~~~~~\n"
            print "Calculating differences between PINs within sets:"
            print "---\n"

            ##
            # THIS LINE GOES "for name in X" --
            # you can change the X to be any of the lists defined at the top
            # of this file to compare different metrics (see above for details).
            # There has to be a better way to designate this,
            # but for now this is good enough :/
            for name in dist_sets:
                hist_of_set(timings, all_sets[name], name)
                mean_std_of_set(timings, all_sets[name], name, "ALL")
                # relevance_within_set(timings, subset, name, "ALL")

            ##
            # Create the formatter using the function to_percent. This multiplies all the
            # default labels by 100, making them all percentages
            formatter = FuncFormatter(to_percent)

            # Set the formatter
            plt.gca().yaxis.set_major_formatter(formatter)

            # Labels on the graph
            plt.ylabel('Frequency')
            plt.xlabel('Interkey Time in ms')
            plt.title('PDF of key latencies across all users - all distances')
            plt.xlim([0,650])
            plt.grid(True)
            legend = plt.legend(loc='center left', bbox_to_anchor=(1, 0.5))

            with cd('plots'):
                plt.savefig('overlaid_all_users.png', bbox_extra_artists=(legend,), bbox_inches='tight')
            plt.clf()

            print "~~~~~~~~~~~~~~~~~~~~~~\n"
            print "Calculating differences between sets:"
            print "---\n"
            relevance_between_sets_from_superset(timings, dist_sets)
            relevance_between_sets_from_superset(timings, dir_one_sets)
            relevance_between_sets_from_superset(timings, dir_two_sets)

##
# Perform all functionality with data from individual users
def main_per_user():
    timings = obtain_timings_per_user()
    timings = filter_timings_per_user(timings)
    i = 1

    for user_data in timings:
        with cd('outputs'):
            with change_stdout('user_' + str(i) + '.out'):
                print "Analyzing user " + str(i) + ":\n"
                print "~~~~~~~~~~~~~~~~~~~~~~\n"
                print "Calculating differences between PINs within sets:"
                print "---\n"

                ##
                # THIS LINE GOES "for name in X" --
                # you can change the X to be any of the lists defined at the top
                # of this file to compare different metrics (see above for details).
                # There has to be a better way to designate this,
                # but for now this is good enough :/
                for name in compare_sets:
                    hist_of_set(user_data, all_sets[name], name)
                    mean_std_of_set(user_data, all_sets[name], name, str(i))
                    # relevance_within_set(user_data, subset, name, str(i))

                ##
                # Create the formatter using the function to_percent. This multiplies all the
                # default labels by 100, making them all percentages
                formatter = FuncFormatter(to_percent)

                # Set the formatter
                plt.gca().yaxis.set_major_formatter(formatter)

                # Labels on the graph
                plt.ylabel('Frequency')
                plt.xlabel('Interkey Time in ms')
                plt.title('Histograms for user ' + str(i))
                plt.xlim([0,750])
                plt.grid(True)
                legend = plt.legend(loc='center left', bbox_to_anchor=(1, 0.5))

                with cd('plots'):
                    plt.savefig('overlaid_user_' + str(i) + '.png', bbox_extra_artists=(legend,), bbox_inches='tight')
                plt.clf()

                print "~~~~~~~~~~~~~~~~~~~~~~\n"
                print "Calculating differences between sets:"
                print "---\n"
                relevance_between_sets_from_superset(user_data, dist_sets)
                relevance_between_sets_from_superset(user_data, dir_one_sets)
                relevance_between_sets_from_superset(user_data, dir_two_sets)

                i += 1

##
# Create the plot of all partitions of users. Not particularly useful
def compare_across_user():
    timings = obtain_timings_per_user()
    timings = filter_timings_per_user(timings)

    with cd('outputs'):
        ##
        # here we use the combinations tool to separate out all
        # the possible ways we can combine users to make one half
        # of the partition (the other half is implicitly defined
        # as its opposite)
        for i in range((len(timings) / 2) + 1):
            for user_list_a in itertools.combinations(list(range(len(timings))), i):
                list_a = set(user_list_a)
                list_b = set(range(len(timings))) - list_a
                timing_set_a = defaultdict(lambda: [])
                timing_set_b = defaultdict(lambda: [])
                
                # pull out all the timings from one half of the partition
                for set_num in list_a:
                    for k, v in timings[set_num].items():
                        timing_set_a[k].extend(v)
                
                # pull out all the timings from the other half
                for set_num in list_b:
                    for k, v in timings[set_num].items():
                        timing_set_b[k].extend(v)

                # plot the two distributions
                # (we only look at dist_one here for simplicity's sake)
                hist_of_set(timing_set_a, all_sets["dist_one"], "Set A")
                hist_of_set(timing_set_b, all_sets["dist_one"], "Set B")

        ##
        # Create the formatter using the function to_percent. This multiplies all the
        # default labels by 100, making them all percentages
        formatter = FuncFormatter(to_percent)

        # Set the formatter
        plt.gca().yaxis.set_major_formatter(formatter)

        # Labels on the graph
        plt.ylabel('Frequency')
        plt.xlabel('Interkey Time in ms')
        plt.title('PDF for user partitions -- dist one only')
        plt.xlim([0,650])
        plt.grid(True)

        with cd('plots'):
            plt.savefig('user_partitions.png', bbox_inches='tight')
        plt.clf()


main_per_user()
main_all()
