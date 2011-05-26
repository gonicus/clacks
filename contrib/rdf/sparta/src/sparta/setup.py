#!/usr/bin/env python

from distutils.core import setup

setup(name='sparta',
		version = '0.82',
		py_modules = ['sparta'],
		author = 'Mark Nottingham',
		author_email = 'mnot@pobox.com',
		url = 'http://www.mnot.net/sw/sparta/',
		description = 'Simple API for RDF',
		long_description = """Sparta is an Python API for RDF that is designed 
to help easily learn and navigate the Semantic Web programmatically. 
Unlike other RDF interfaces, which are generally triple-based, Sparta 
binds RDF nodes to Python objects and RDF arcs to attributes of those 
Python objects.""",
		license = 'MIT',
		classifiers = [
		  'License :: OSI Approved :: MIT License',
		  'Operating System :: OS Independent',
		  'Programming Language :: Python',
		  'Topic :: Software Development :: Libraries :: Python Modules',
		],
	)
