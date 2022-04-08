from textblob import TextBlob
import nltk
import os

def load_blacklist(fname):
    blacklist = []
    with open(fname, 'r') as f:
        for line in f:
            word = line.strip('\n').lower()
            blacklist.append(word)
    return blacklist

def write_preprocessed_blacklist():
     """
     Load our blacklist, and preprocess it (for each offensive phrase add plural versions, 
     punctuation variants etc). Write the full preprocessed set to file.
     """

     outfile = os.path.join(os.path.dirname(__file__), '../../../chirpy/core/offensive_classifier/data_preprocessed/offensive_phrases_preprocessed.txt')

     # Load and preprocess our additional blacklist
     blacklist_file_path = os.path.join(os.path.dirname(__file__), '../../../chirpy/core/offensive_classifier/data_original/full-list-of-bad-words_text-file_2018_07_30.txt')
     blacklist = load_blacklist(blacklist_file_path)  # list of strings

     # Merge into set
     blacklist = set(blacklist)

     # Make some alternate versions
     for phrase in list(blacklist):
         phrase_words = phrase.split()
         if len(phrase_words) > 1:  # if it's a multi word phrase, trying sticking the words together or hyphenating
             print(phrase, ''.join(phrase_words))
             blacklist.add(''.join(phrase_words))
             print(phrase, '-'.join(phrase_words))
             blacklist.add('-'.join(phrase_words))
         if '-' in phrase and '--' not in phrase:  # if it contains hyphens (e.g. jerk-off but not f--k), try sticking the words together or spacing them
             print(phrase, phrase.replace('-', ''))
             blacklist.add(phrase.replace('-', ''))
             print(phrase, ' '.join(phrase.replace('-', ' ').split()))
             blacklist.add(' '.join(phrase.replace('-', ' ').split()))

     # Write to file
     print(f'writing {len(blacklist)} phrases to {outfile}...')
     with open(outfile, 'w') as f:
         for phrase in sorted(list(blacklist)):
             f.write(phrase + '\n')
     print('done')

if __name__ == "__main__":
    write_preprocessed_blacklist()