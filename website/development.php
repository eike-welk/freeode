<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">
<html>

<head>
  <title>Free ODE</title>
  <meta name="GENERATOR" content="Quanta Plus">
  <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
  <meta name="KEYWORDS" content="freeode, simulation, numerical math, python, ODE, differential equations">
  <META name="Author" content="Eike Welk">
  <link rel="stylesheet" type="text/css" href="freeode.css">
</head>


<body>
<!--Title-->
<?php if( file_exists("header.html") ){ include("header.html"); } ?>

<!--Navigation-->
<?php if( file_exists("menu-left.html") ){ include("menu-left.html"); } ?>


<div id="contents">
  <h1>Development</h1>
  <p>
    The compiler is a Python program that uses the
    <A href="http://pyparsing.wikispaces.com/">Pyparsing</A>
    library for parsing.
    Most of the code is in the package 'freeode' except for a
    small main script: 'simlc'.
  </p>
  <p>
    The generated Python program uses also modules of the freeode package
    as a runtime library.
    The
    <A href="http://numpy.scipy.org/">NumP</A>
    and
    <A href="http://www.scipy.org/">SciPy</A>
    libraries are used for numerical computations and plotting.
  </p>


  <h2>Dependencies</h2>
  <p>
  The following dependencies exist for the compiler and the runtime libraries:
  </p>
  <p>
    <table>
      <tbody>
        <tr>
          <td>Name</td>
          <td>What</td>
          <td>Linux</td>
          <td>Windows</td>
        </tr>

        <tr>
          <td><A href="http://www.python.org">Python</A></td>
          <td>programming language</td>
          <td>usually already installed</td>
          <td>available in binary packages especially suited for scientific development</td>
        </tr>

        <tr>
          <td><A href="http://pyparsing.wikispaces.com/">pyparsing</A></td>
          <td>library for parsers</td>
          <td>only sources, easy install</td>
          <td>only sources, easy install</td>
        </tr>

        <tr>
          <td><A href="http://numpy.scipy.org/">NumPy</A></td>
          <td>array object, linear algebra</td>
          <td>binary packages exist for <strong>most</strong> distributions</td>
          <td>comes with scientific Python distribution</td>
        </tr>

        <tr>
          <td><A href="http://www.scipy.org/">SciPy</A></td>
          <td>scientific algorithms</td>
          <td>binary packages exist for <strong>some</strong> distributions</td>
          <td>comes with scientific Python distribution</td>
        </tr>
      </tbody>
    </table>
  </p>



  <h2>Linux</h2>

  <h3>Getting and Installing the Libraries</h3>
  <h4>Pyparsing</h4>
  <A href="http://sourceforge.net/project/showfiles.php?group_id=97203">download</A>
  <h4>NumPy</h4>
  <h4>SciPy</h4>
  <h3>Getting the sources</h3>
  <p>
    The latest version of all of the project's files, is available from the subversion
    repository at BerliOS.
  </p>
  <p>
    To check out (download) only the compiler, type the following in a shell window:
  </p>
  <div id="code">
    <pre> svn checkout svn://svn.berlios.de/freeode/trunk/freeode_py </pre>
  </div>

  <p>To check out everything, including website, examples and more, do:</p>
  <div id="code">
    <pre>
svn checkout svn://svn.berlios.de/freeode/trunk
    </pre>
  </div>

  <h3>Compiling the sources</h3>
  <p>
    In the directory 'freeode_cpp' you will find a Kdevelop project file.
    The SIML compiler is currently developed with the IDE Kdevelop.
  </p>
  <p>
    If you just want to compile the latest soures here are the necessary steps:
    Open a shell window and  change into the directory 'freeode_cpp'
    (which you just downloaded through subversion).
    Type the commands given below.
    Some commands will take quite a while to complete.
    <br>
    <strong>Warning!</strong> Currently the installation goes into the KDE
    directory. This won't harm, but is quite stupid.
    </p>
  <div id="code">
    <pre>
make -f Makefile.cvs
./configure
make
su
make install
    </pre>
  </div>

  <p>
    From time to time you'll need to regenerate the file 'simulatorbase.h'
    from the file 'simulatorbase.py' with the following commands:
    </p>
  <div id="code">
    <pre>
cd src
python py2c_string.py
    </pre>
  </div>


  <h2>Windows</h2>
  <p>
    No attempt has been made to port the compiler
    to Windows, since the development happens on Linux.
    In principle however, everything should work on Windows. The
    <A href="http://www.python.org">Python</A>
    language and the necessary libraries (
    <A href="http://www.boost.org/">Boost</A>,
    <A href="http://numeric.scipy.org/">NumPy</A>,
    <A href="http://www.scipy.org/">SciPy</A>)
    are all available for Windows. So you're on your own there.
  </p>
  <p>
    There is a free Python package from <A href="http://www.enthought.com/">Enthought</A>.
    It contains <strong>NumPy</strong> and <strong>SciPy</strong>, (plus much more scientific Python stuff).
  </p>
  <p>
    If you have a C++ compiler for Windows and some time, you could probably port the compiler
    to Windows with minimum effort. The Python part needs no change, since Python promises to
    be platform independent.
    I would be very glad to receive patches and binaries.
  </p>
  <p>
    Graphs (<A href="http://gnuplot-py.sourceforge.net/">Gnuplot.py</A>) are surely an issue.
    If you port the compiler to Windows I'll change the graph library to whatever is commonly
    available on Windows.
  </p>
</div>

<!--footer with the required berlios image-->
<?php if( file_exists("footer.html") ){ include("footer.html"); } ?>

</body>
</html>
