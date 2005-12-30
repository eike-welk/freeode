# set the include path for X, qt and KDE
INCLUDES = $(all_includes)

# these are the headers for your project
noinst_HEADERS = parser.h siml_skip_grammar.h siml_code_model.h \
	siml_python_generator.h siml_ps_process.h siml_ps_toplevel.h siml_error_generator.h \
	siml_ps_model.h siml_ps_name.h

# let automoc handle all of the meta source files (moc)
METASOURCES = AUTO

messages: rc.cpp
	$(EXTRACTRC) `find . -name \*.ui -o -name \*.rc` > rc.cpp
	$(XGETTEXT) *.cpp -o $(podir)/sim_lang.pot

KDE_ICON = AUTO

#########################################################################
# APPLICATION SECTION
#########################################################################
# this is the program that gets installed.  it's name is used for all
# of the other Makefile.am variables
bin_PROGRAMS = sim_lang

# the application source, library search path, and link libraries
sim_lang_SOURCES = main.cpp parser.cpp siml_python_generator.cpp \
		siml_code_model.cpp siml_error_generator.cpp
sim_lang_LDFLAGS = $(KDE_RPATH) $(all_libraries)
sim_lang_LDADD = $(LIB_KDEUI)

# this is where the desktop file will go 
shelldesktopdir   = $(kde_appsdir)/Utilities
shelldesktop_DATA = sim_lang.desktop

# this is where the shell's XML-GUI resource file goes
shellrcdir   = $(kde_datadir)/sim_lang
shellrc_DATA = sim_langui.rc

