#!/usr/bin/env python
# Generates the API documentation.
import os, re, sys

doc_dir  = 'api'
doc_file = os.path.join(doc_dir, 'SpiffSignal.py')
files    = ['../src/SpiffSignal/Trackable.py'] # Order matters - can't resolve inheritance otherwise.
classes  = [os.path.splitext(os.path.basename(file))[0] for file in files]
classes  = ['(?:SpiffSignal.)?' + cl for cl in classes]

# Concatenate the content of all files into one file.
if not os.path.exists(doc_dir):
    os.makedirs(doc_dir)
remove_re = re.compile(r'^from (' + '|'.join(classes) + r') * import .*')
fp_out    = open(doc_file, 'w')
for file in files:
    fp_in = open(file, 'r')
    for line in fp_in:
        if not remove_re.match(line):
            fp_out.write(line)
    fp_in.close()
fp_out.close()

os.system('epydoc ' + ' '.join(['--html',
                                '--parse-only',
                                '--no-private',
                                '--no-source',
                                '--no-frames',
                                '--inheritance=grouped',
                                '-v',
                                '-o %s' % doc_dir, doc_file]))
