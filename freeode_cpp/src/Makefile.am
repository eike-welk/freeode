# set the include path found by configure
INCLUDES = $(all_includes)

# these are the headers for your project
noinst_HEADERS = siml_code_model.h siml_ps_toplevel.h siml_error_generator.h \
	siml_ps_model.h siml_ps_name.h siml_ps_skip.h siml_cmpath.h siml_ps_path.h \
	siml_ps_formula.h siml_cmformula.h siml_ps_equation.h siml_ps_memory_definition.h \
	siml_cmerror.h siml_pygenmain.h siml_cmmemaccess.h siml_ps_mem_access.h \
	siml_pyformulaconverter.h simulatorbase.h siml_cmmodelintermediate.h siml_globaldef.h \
	siml_ps_main_object.h

#########################################################################
# APPLICATION SECTION
#########################################################################
# this is the program that gets installed.  it's name is used for all
# of the other Makefile.am variables
bin_PROGRAMS = siml

# the application source, library search path, and link libraries

AM_CXXFLAGS = -fexceptions
siml_LDFLAGS = $(all_libraries)
siml_LDADD = -lboost_date_time
siml_SOURCES = main.cpp siml_cmerror.cpp siml_cmformula.cpp siml_cmmemaccess.cpp\
	siml_cmmodelintermediate.cpp siml_cmpath.cpp siml_code_model.cpp\
	siml_ps_main_object.cpp siml_ps_name.cpp siml_pyformulaconverter.cpp\
	siml_pygenmain.cpp siml_pyprocessgenerator.cpp
