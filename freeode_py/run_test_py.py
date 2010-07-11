# -*- coding: utf-8 -*-
#Run all tests with "py.test"
#"py.test" is a program to find tests and to run them.

import os

#Run tests on 2 CPUs and produce only short back trace; run all tests.
os.system("time py.test -n 2 --tb=short --report=skipped")
#os.system("py.test --tx 2*popen//python=pypy --dist=load --tb=short --report=skipped")


#Run fewer tests
#os.system("py.test -n 2 --tb=short "
#          "freeode/test_util.py freeode/test_ast.py freeode/test_simlparser.py")
#os.system("py.test -n 2 --tb=short --report=skipped freeode/test_1_interpreter.py")
#os.system("py.test -n 2 --tb=short freeode/test_2_interpreter.py")


#os.system('py.test -n 2 --tb=short '
#          'freeode/test_1_interpreter.py '
#          'freeode/test_2_interpreter.py '
#          'freeode/test_3_interpreter_errors.py ')
