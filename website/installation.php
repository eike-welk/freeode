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
  <h1>Installation</h1>
  <h2>Dependencies</h2>
  <p>
    You need the Python language, and libraries below.
  </p>
  <p>
    <table>
      <tbody>
        <tr>
          <td><A href="http://www.boost.org/">Boost</A></td>
          <td>&nbsp;&nbsp;C++ lib</td>
          <td>&nbsp;&nbsp;usually present on Linux</td>
        </tr>
        <tr>
          <td><A href="http://www.python.org">Python</A></td>
          <td>&nbsp;&nbsp;Programming language</td>
          <td>&nbsp;&nbsp;usually present on Linux</td>
        </tr>
        <tr>
          <td><A href="http://numeric.scipy.org/">NumPy</A></td>
          <td>&nbsp;&nbsp;Python lib</td>
          <td>&nbsp;&nbsp;often present on Linux</td>
        </tr>
        <tr>
          <td><A href="http://www.scipy.org/">SciPy</A></td>
          <td>&nbsp;&nbsp;Python lib</td>
          <td></td>
        </tr>
        <tr>
          <td><A href="http://gnuplot-py.sourceforge.net/">Gnuplot.py</A></td>
          <td>&nbsp;&nbsp;Python lib</td>
          <td></td>
        </tr>
      </tbody>
    </table>
  </p>

  <h2>Linux</h2>
  <h3>Compiling from sources</h3>
  <p>TODO: create source package.</p>
  <p>
    Alternatively you could download the sources with subversion. This is explained in
    the <A href="development.html">development</A> section.
  </p>

  <h3>Binary Package</h3>
  <p>
    If you don't feel like compiling the program you can download a binary version.
    It was compiled on a Suse 9.3 system with <strong>gcc version 3.3.5</strong>.

    <ul>
      <li>
        Download the file 'siml-binary-0.2.0.tar.gz' from the
        <A href="https://developer.berlios.de/project/showfiles.php?group_id=5610">download</A>
        section
      </li>
      <li>Extract the executable from the archive. This results in a file named 'siml'</li>
      <li>Copy the executable to a directory in your PATH. Usually: '/usr/local/bin'</li>
      <li>Use the compiler: siml filename.siml</li>
    </ul>
  </p>

  <h2>Windows</h2>
  <p>Currently there is no Windows version, although porting should be easy.</p>

  <h2>Examples</h2>
  <p>
    There is also a package with example files in the
    <A href="https://developer.berlios.de/project/showfiles.php?group_id=5610">download</A>
    section: 'models.tar.gz'.
  </p>
</div>


<!--footer with the required berlios image-->
<?php if( file_exists("footer.html") ){ include("footer.html"); } ?>

</body>
</html>
