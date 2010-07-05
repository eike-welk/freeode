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
    <li><A href="installation.php#top">Top</A></li>
    <li><A href="installation.php#install-python">Python</A></li>
    <li><A href="installation.php#install-numpy-scipy-matplotlib">
                   NumPy, SciPy, Matplotlib</A></li>
    <li><A href="installation.php#install-freeode">Freeode</A></li>
  </ul>
</div>


<div id="contents">
  <A name="top"></A>
  <h1>Installation</h1>
  <h2>Dependencies</h2>
  <p>
    The compiler only needs the
    <A href="http://www.python.org/">Python</A> language.
    The generated Python programs additionally need the
    <A href="http://numpy.scipy.org/">NumPy</A>
    ,
    <A href="http://www.scipy.org/">SciPy</A>
    and
    <A href="http://matplotlib.sourceforge.net/">Matplotlib</A>
    libraries for numerical computations and plotting. (The compiler contains 
    a modified copy of the 
    <A href="http://pyparsing.wikispaces.com/">Pyparsing</A> library, which 
    therefore does not need to be installed.)
  </p>

  <p>
  Here is a table of the dependencies:
  </p>
  <p>
    <table border="1">
      <tbody>
        <tr>
          <td><em>Name</em></td>
          <td><em>What</em></td>
          <td><em>Linux</em></td>
          <td><em>Windows</em></td>
        </tr>

        <tr>
          <td><A href="http://www.python.org">Python</A></td>
          <td>programming language</td>
          <td>usually already installed</td>
          <td>special binary distribution for scientists available</td>
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

  <!--============================== Installing Dependencies ========================================-->
  <h2>Installing Dependencies</h2>

  <!--========================== Python ==========================-->
  <A name="install-python"></A>
  <h3>Python</h3>
    <p>Freeode needs <strong>Python</strong> version between 
	<strong>2.5</strong> and <strong>2.7</strong> (not Python 3.x).</p>
  <h4>Linux</h4>
  <p>
    <A href="http://www.python.org/">Python</A>
    should be already installed on your system.
    If not, install it with your software management program (package manager).
   </p>
  <h4>Windows</h4>
  <p>
    Most probably you will need to install Python on your computer.
    For Windows there are binary distributions, which are especially made for 
    scientists:

  </p>
  <ul>
    <li>Python(x,y): <A href="http://www.pythonxy.com/">download</A>.</li>
  </ul>
  <ul>
    <li>Enthought Python: <A href="http://code.enthought.com/enthon/">download</A>.</li>
  </ul>
  <p>
    These distributions contain very many useful features for scientific work.
    Linux users (me) will envy you. I recommend that you install one of them.
  </p>
  <p>
    The
    <A href="http://www.activestate.com/Products/ActivePython/">ActivePython</A> 
    distribution however seems not to contain the necessary libraries.
 </p>


  <!--========================== Numpy, SciPy, Matplotlib ==========================-->
  <A name="install-numpy-scipy-matplotlib"></A>
  <h3>NumPy, SciPy, Matplotlib</h3>
  <p>
	The
	<A href="http://www.scipy.org/">SciPy</A>
	documentation contains
	<A href="http://www.scipy.org/Installing_SciPy">instructions</A>
	to install NumPy and SciPy. These cover Windows, Mac-OS, and a variety of 
    Linux distributions.
  </p>
  <p>  
	The Matplotlib
	<A href="http://matplotlib.sourceforge.net/">website</A>
	contains some
	<A href="http://matplotlib.sourceforge.net/installing.html">installation instructions</A>.
	Here is their
	<A href="http://sourceforge.net/project/showfiles.php?group_id=80706">download area</A>.
  </p>
  <h4>Linux</h4>
  <p>Many distributions contain packages Numpy, SciPy, and Matplotlib, which 
  then appear in the package manager. I specifically know of:</p>
  <ul>
    <li>
      <A href="http://www.opensuse.org/">openSuse</A>:
      A repository for Numpy, SciPy, and Matplotlib is here:
      <A href="http://software.opensuse.org/download/science/">
        http://software.opensuse.org/download/science/
      </A>.
      The directory that matches your version of openSuse can be added as an
      installation source to Yast.
    </li>
    <li>
      <A href="http://www.ubuntu.com/">Ubuntu</A>:
      Packages for Numpy, SciPy, and Matplotlib are in the 
      <strong>Universe</strong> 
      <A href="http://www.ubuntu.com/ubuntu/components">component</A>.
      Universe has to be enabled in the package manager, then packages
      for Numpy, SciPy, and Matplotlib appear in the package manager together
      with a large number of other packages.
    </li>
  </ul>
  <h4>Windows</h4>
  <p>
    NumPy, SciPy and Matplotlib are included in both recommended Python 
    distributions: 
    <A href="http://www.pythonxy.com/">Python(x,y)</A> and
    <A href="http://code.enthought.com/enthon/">Enthon</A>.
  </p>


  <!--============================== Installing Freeode ================================-->
  <A name="install-freeode"></A>
  <h2>Installing Freeode</h2>
  <p>
    Freeode is distributed in several different formats: *.rpm, *.exe, *.tar.gz 
    and *.zip. Files in *.rpm and *.exe can usually be installed by clicking 
    on them. To use *.tar.gz and *.zip files you need to enter some 
    commands on the command line to perform the installation.
  
    Get the latest source <strong>tar.gz</strong> package
    (for example <strong>freeode-0.3.0.tar.gz</strong>) from the
    <A href="https://developer.berlios.de/project/showfiles.php?group_id=5610">download</A>
    section and and extract the contents.
    Then run the setup script (<strong>python setup.py install</strong>).
    Ready.
  </p>
  <p>
    You can also create binary packages (<strong>rpm, exe</strong>) with this script;
    to install them with the operating system's software management tool.
    Look at the comments inside the <strong>setup.py</strong> script.
  </p>
  <p>
    Alternatively you may try the binary packages and install them with your software
    management tool.
  </p>
  </p>
  <h4>Linux</h4>
  <ul>
    <li>
      <A href="https://developer.berlios.de/project/showfiles.php?group_id=5610">Download</A>
      the latest source package (<strong>*.tar.gz</strong>).
    </li>
    <li>Open a shell window. Type:</li>
  </ul>
  <div id="code">
    <pre>
> cd **where you put the downloaded *.tar.gz file**
> su                               #become root
Password:
> tar xvf freeode-0.3.0.tar.gz     #extract package contents
> cd freeode-0.3.0/                #enter extracted directory
> python setup.py install          #run installation script
    </pre>
  </div>
  <h4>Windows</h4>
  <p>Someone please try out the Windows installer! I want to know if it works.</p>
  <ul>
    <li>
      <A href="https://developer.berlios.de/project/showfiles.php?group_id=5610">Download</A>
      the latest source package (<strong>*.tar.gz</strong>).
    </li>
    <li>
      Extract the contents of the package.
      You can for example use the
      <A href="http://www.winzip.com/">Winzip</A>
      program.
    </li>
    <li>Open a DOS box. <em>How is this really called?</em></li>
    <li>Got to the directory to where you downloaded the package.</li>
    <li>
      Run the installation script: <strong>python setup.py install</strong>
      (You might need administrator privileges.)
    </li>
 </ul>

</div>


<!--footer with the required berlios image-->
<?php if( file_exists("footer.html") ){ include("footer.html"); } ?></body>
</html>
