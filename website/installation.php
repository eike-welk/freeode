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
    You need the
    <A href="http://www.python.org/">Python</A>
    language and some libraries:
    The compiler uses the
    <A href="http://pyparsing.wikispaces.com/">Pyparsing</A>
    library.
    The generated Python program needs the
    <A href="http://numpy.scipy.org/">NumPy</A>
    ,
    <A href="http://www.scipy.org/">SciPy</A>
    and
    <A href="http://matplotlib.sourceforge.net/">Matplotlib</A>
    libraries for numerical computations and plotting.
  </p>

  <p>
  Here is a table of the dependencies:
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
          <td>special binary distribution for scientist availlable</td>
        </tr>

        <tr>
          <td><A href="http://pyparsing.wikispaces.com/">pyparsing</A></td>
          <td>library for parsers</td>
          <td>only sources</td>
          <td>only sources</td>
        </tr>

        <tr>
          <td><A href="http://numpy.scipy.org/">NumPy</A></td>
          <td>array object, linear algebra</td>
          <td>binary packages for <strong>most</strong> distributions</td>
          <td>comes with scientific Python distribution</td>
        </tr>

        <tr>
          <td><A href="http://www.scipy.org/">SciPy</A></td>
          <td>scientific algorithms</td>
          <td>binary packages for <strong>some</strong> distributions</td>
          <td>comes with scientific Python distribution</td>
        </tr>

        <tr>
          <td><A href="http://matplotlib.sourceforge.net/">Matplotlib</A></td>
          <td>plotting</td>
          <td>binary packages for <strong>some</strong> distributions</td>
          <td>comes with scientific Python distribution</td>
        </tr>
      </tbody>
    </table>
  </p>


  <h2>Installing Dependencies</h2>
  <h3>Python</h3>
  <h3>Pyparsing</h3>
  <h3>Numpy</h3>
  <h3>SciPy</h3>
  <h3>Matplotlib</h3>


  <h2>Installing Freeode</h2>
  <p>The installation of the freeode package is very easy:</p>
  <p>
    Get the latest source <strong>tar.gz</strong> package
    (for example <strong>freeode-0.3.0.tar.gz</strong>) from the
    <A href="https://developer.berlios.de/project/showfiles.php?group_id=5610">download</A>
    section and and extract the contents.
    Enter the generated directory and run the setup script (<strong>python setup.py install</strong>).
    Ready.
  </p>
  <p>
    You can also create binary packages (<strong>rpm deb? exe</strong>) with this script;
    to install them with the operating system's software management tool.
    Look at the comments inside the <strong>setup.py</strong> script.
  </p>
  </p>
  <h4>Linux</h4>
  tar xvf ....
  <h4>Windows</h4>
  <p>
    Extract the contents of the
    <A href="https://developer.berlios.de/project/showfiles.php?group_id=5610">downloaded</A>
    <strong>tar.gz</strong> file.
    You can for example use the
    <A href="http://www.winzip.com/">Winzip</A>
    program.
  </p>
  <p>TODO: see how other projects give generic installation instructions.</p>

</div>


<!--footer with the required berlios image-->
<?php if( file_exists("footer.html") ){ include("footer.html"); } ?>

</body>
</html>
