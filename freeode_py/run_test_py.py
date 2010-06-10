# -*- coding: utf-8 -*-
#Run all tests with "py.test"
#"py.test" is a program to find tests and to run them.

import os
#run tests on 2 CPUs and produce only short back trace.
os.system("py.test -n 2 --tb=short")

#os.system("py.test -n 2 --tb=short freeode/test_1_interpreter.py")