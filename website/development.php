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


<div id="navigation_page">
  <ul>
    <li>Installation</li>
    <li><A href="development.php#top">Top</A></li>
    <li><A href="development.php#get-the-sources">Get the Sources</A></li>
  </ul>
</div>


<div id="contents">

  <A name="top"></A>
  <h1>Development</h1>
  <p>
    The compiler is a Python program that uses the
    <A href="http://pyparsing.wikispaces.com/">Pyparsing</A>
    library for parsing.
    The generated Python program uses the
    <A href="http://numpy.scipy.org/">NumPy</A>
    ,
    <A href="http://www.scipy.org/">SciPy</A>
    and
    <A href="http://matplotlib.sourceforge.net/">Matplotlib</A>
    libraries for numerical computations and plotting.
    For a detailed discussion of the dependencies see the
    <A href="installation.php">installation</A>
    instructions.
  </p>

  <p>
    Python promises to be highly platform independent.
    Therfore everything should work on Windows exacly as it works on Linux.
  </p>

  <p>
    Development currently happens on Linux only.
    The
    <A href="http://pydev.sourceforge.net/">Pydev</A>
    extension for
    <A href="http://www.eclipse.org/">Eclipse</A>
    is used as the IDE. Pydev analyzes the program and can complete Python code much
    better than any other free IDE I know. It uses
    <A href="www.logilab.org/857">Pylint</A>
    to flag errors and bad coding practice.
    Eclipse and Pydev are written in Java,
    and should therfore work on Windows
    as well.
  </p>
  <p>
    Pydev's code completion is quite slow;
    it can unfortunately not usefully work when all of NumPy
    has been imported. It will then always hang for ~30s before it can show a list of
    possible completions (on Pentium M 1.4 GHz).
    Pydev's slowness is the reason why the code conains lines like this:
    <div id="code">
      <pre>from numpy import array, linspace, zeros, shape, ones, resize</pre>
    </div>
    instead of:
    <div id="code">
      <pre>from numpy import *</pre>
    </div>
  </p>


  <A name="get-the-sources">
  </A><h2>Getting the sources</h2>
  <p>
    The latest version of all of the project's files, is available from the subversion
    repository at BerliOS.
  </p>
  <p>
    To check out (download) only the Python code, type the following in a shell window:
  </p>
  <div id="code">
    <pre>svn checkout svn://svn.berlios.de/freeode/trunk/freeode_py </pre>
  </div>

  <p>
    To check out everything, including website, and some additional documentation, do:
  </p>
  <div id="code">
    <pre>svn checkout svn://svn.berlios.de/freeode/trunk</pre>
  </div>

  </div>


</div>

<!--footer with the required berlios image-->
<?php if( file_exists("footer.html") ){ include("footer.html"); } ?>

</body>
</html>
