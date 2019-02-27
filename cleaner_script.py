import json
import csv
import itertools
from Levenshtein import editops, matching_blocks, distance

def compute_taxonomy_values(target, transcribed, stream):
    """ Function that computes and returns the different taxonomy values as 
    described by Soukoreff and MacKenzie (https://www.yorku.ca/mack/chi03)
    """

    # Compute the Levenshtein distance (Incorrect Not Fixed (INF))
    ops = editops(target, transcribed)
    inf = len(ops)

    # The number of correct keystrokes (C) is the difference between 
    # the length of the transcribed text and INF
    blocks = matching_blocks(ops, target, transcribed)
    c = sum([block[2] for block in blocks])

    # The number of fixes (F) is equal to the number of 'delete' 
    # present in the input stream
    f = [x for x in stream].count('delete')

    # The number of incorrect input that were fixed (IF) is the number of 
    # non-delete characters present in the input stream but not in the 
    # transcribed text
    _if = [x for x in stream if x != 'delete']
    _if = distance(''.join(_if), transcribed)

    return (inf, c, f, _if)


def test_compute_taxonomy_values():
    """ Simple test based on the example provided by Soukoreff and MacKenzie in 
    https://www.yorku.ca/mack/chi03
    """

    inf, c, f, _if = compute_taxonomy_values(
        'the quick brown', 
        'th quick brpown', 
        ['t', 'h', ' ', 'q', 'u', 'i', 'x', 'x', 'delete',
        'delete', 'c', 'k', ' ', 'b', 'r', 'p', 'o', 'w', 'n'])

    assert inf == 2, 'inf was {} was expecting 2'.format(inf)
    assert c == 14, 'c was {} was expecting 14'.format(c)
    assert f == 2, 'f was {} was expecting 1'.format(f)
    assert _if == 1, '_if was {} was expecting 1'.format(_if)


def compute_average_time(stream):
    deltas = [a - b for (a, b) in zip(stream[1:], stream[:-1])]
    return round(sum(deltas) / len(deltas))
    

if __name__ == '__main__':
    """ Script that reads the data from JSON files and outputs a CSV file with 
    relevant computed values ready for analysis
    """

    # Open the output file
    output_path = 'data/clean/clean-data.csv'
    output_file = open(output_path, 'w')
    fields = ['uid', 'participant', 'type', 'feedback', 
            'trial', 'avg_time(ms)', 'INF', 'C', 'F', 'IF']
    writer = csv.DictWriter(output_file, fields, lineterminator='\n')
    writer.writeheader()

    # Loop over all result files
    uid = 1
    results_path = 'data/clean/results-participant-{}/results-{}-38mm-{}.json'
    iterable = itertools.product(
        [1, 2, 3, 4], 
        ['normal', 'zoom'], 
        ['false', 'true']
    )
    for participant, kb_type, feedback in iterable:

        # Load results into dictionaries
        with open(results_path.format(participant, kb_type, feedback), 'r') as file:
            results = json.load(file)

        # Loop over all trials
        for (i, trial) in enumerate(results['trials']):
            inf, c, f, _if = compute_taxonomy_values(
                trial['targetPhrase'], 
                trial['inputPhrase'], 
                [x['input'] for x in trial['inputs']])
            
            timestamp_stream = [x['timestamp'] for x in trial['inputs']]
            avg_time = compute_average_time(timestamp_stream)
            
            # Write results to file
            results = [
                uid, 
                participant, 
                kb_type, 
                feedback, 
                i+1, 
                avg_time, 
                inf, 
                c, 
                f, 
                _if
            ]
            _ = writer.writerow(dict(zip(fields, results)))
            uid += 1
            
    # Close the output file
    output_file.close()
