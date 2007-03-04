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
    <li><A href="installation.php#install-pyparsing">Pyparsing</A></li>
    <li><A href="installation.php#install-numpy-scipy">NumPy SciPy</A></li>
    <li><A href="installation.php#install-matplotlib">Matplotlib</A></li>
    <li><A href="installation.php#install-freeode">Freeode</A></li>
  </ul>
</div>


<div id="contents">
  <A name="top"></A>
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
          <td>special binary distribution for scientist available</td>
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

  <!--============================== Installing Dependencies ========================================-->
  <h2>Installing Dependencies</h2>

  <strong>
    TODO: Add generic installation instructions for simple Python packages.
    Shorten pyparsing and Freeode instructions.
  </strong>

  <!--========================== Python ==========================-->
  <A name="install-python"></A>
  <h3>Python</h3>
  <h4>Linux</h4>
  <p>
    <A href="http://www.python.org/">Python</A>
    should be already installed on your system.
    If not, install it with your software management program.
    Freeode needs <strong>Python</strong> version <strong>2.4</strong> or higher.</p>
  <h4>Windows</h4>
  <p>
    Most probably you will need to install Python on your computer.
    For Windows there is a binary distributions, which is especially made for scientists:

  </p>
  <ul>
    <li>Enthought Python: <A href="http://code.enthought.com/enthon/">download</A>.</li>
  </ul>
  <p>
    It contains very many usefull features for scientific work.
    Linux users (me) will envy you. I recommend that you install this distribution.
  </p>
  <p>
    There is also the
    <A href="www.activestate.com/Products/ActivePython/">ActivePython</A> distribution.
    Dear readers, does this distribution contain NumPy, SciPy, and Matplotlib?
    <em>Mail to eike at users.sourceforge.net</em>
 </p>


  <!--========================== Pyparsing ==========================-->
  <A name="install-pyparsing"></A>
  <h3>Pyparsing</h3>
  <p>
    Get the latest source <strong>tar.gz</strong> package
    (for example <strong>pyparsing-1.4.5.tar.gz</strong>) from the
    <A href="http://sourceforge.net/project/showfiles.php?group_id=97203">download</A>
    section and and extract the contents.
    Then run the setup script (<strong>python setup.py install</strong>).
    Ready.
  </p>
  <p>
    Alternatively you may try the binary packages and install them with your software
    management tool.
  </p>
  </p>
  <h4>Linux</h4>
  <ul>
    <li>
      <A href="http://sourceforge.net/project/showfiles.php?group_id=97203">Download</A>
      the latest source package (<strong>*.tar.gz</strong>).
    </li>
    <li>Open a shell window. Type:</li>
  </ul>
  <div id="code">
    <pre>
> cd **where you put the downloaded *.tar.gz file**
> su                                #become root
Password:
> tar xvf pyparsing-1.4.5.tar.gz    #extract package contents
> cd pyparsing-1.4.5/               #enter extracted directory
> python setup.py install           #run installation script
    </pre>
  </div>
  <h4>Windows</h4>
  <ul>
    <li>
      <A href="http://sourceforge.net/project/showfiles.php?group_id=97203">Download</A>
      the Windows installer (<strong>*.exe</strong>).
    </li>
    <li> Click on it. </li>
  </ul>

  <!--========================== Numpy, SciPy ==========================-->
  <A name="install-numpy-scipy"></A>
  <h3>NumPy, SciPy</h3>
  <p>
    The
    <A href="http://www.scipy.org/">SciPy</A>
    documentation contains
    <A href="http://www.scipy.org/Installing_SciPy">instructions</A>
    to install NumPy and SciPy. These cover Windows, Mac-OS, and a variety of Linux distributions.
  </p>
  <h4>Linux</h4>
  <p>Binary distributions I know of:</p>
  <ul>
    <li>
      <A href="http://www.opensuse.org/">openSuse</A>:
      A repository for Numpy, SciPy, and Matplotlib is here:
      <A href="http://software.opensuse.org/download/science/">
        http://software.opensuse.org/download/science/
      </A>.
      The directories can be added as installation sources to Yast.
    </li>
    <li>
      <A href="http://www.ubuntu.com/">Ubuntu</A>:
      Packages for Numpy, SciPy, and Matplotlib are in the Universe
      <A href="http://www.ubuntu.com/ubuntu/components">component</A>.
    </li>
  </ul>
  <p>
    It is relatively easy to build both packages from sources.
    Look at these
    <A href="http://www.scipy.org/Installing_SciPy/BuildingGeneral">instructions</A>
    that focus on building the underlying linear algebra libraries.
    Some problems originate from the current state of free Fortran compilers:
    The <A href="http://gcc.gnu.org/">GCC</A>
    project changed its Fortran compiler from
    <A href="http://gcc.gnu.org/wiki/GFortranG77">g77</A>
    to the newer
    <A href="http://gcc.gnu.org/wiki/GFortran">gfortran</A>
    compiler.
    Both compilers need different command line options and runtime libraries.
  </p>
  <h4>Windows</h4>
  <p>
    NumPy and SciPy (and Matplotlib) are included in Enthought's
    <A href="http://code.enthought.com/enthon/">Python distribution</A>,
    which I recommend.
  </p>


  <!--========================== Matplotlib ==========================-->
  <A name="install-matplotlib"></A>
  <h3>Matplotlib</h3>
  The Matplotlib
  <A href="http://matplotlib.sourceforge.net/">website</A>
  contains some
  <A href="http://matplotlib.sourceforge.net/installing.html">installation instructions</A>.
  Here is their
  <A href="http://sourceforge.net/project/showfiles.php?group_id=80706">download area</A>.
  <h4>Linux</h4>
  <p>Binary distributions I know of:</p>
  <ul>
    <li>
      <A href="http://www.opensuse.org/">openSuse</A>:
      A repository for Numpy, SciPy, and Matplotlib is here:
      <A href="http://software.opensuse.org/download/science/">
        http://software.opensuse.org/download/science/
      </A>.
      The directories can be added as installation sources to Yast.
    </li>
    <li>
      <A href="http://www.ubuntu.com/">Ubuntu</A>:
      Packages for Numpy, SciPy, and Matplotlib are in the Universe
      <A href="http://www.ubuntu.com/ubuntu/components">component</A>.
    </li>
  </ul>
  <h4>Windows</h4>
  <p>
    Matplotlib (and NumPy, SciPy) are included in Enthought's
    <A href="http://code.enthought.com/enthon/">Python distribution</A>
    which I recommend.
  </p>



  <!--============================== Installing Freeode ================================-->
  <A name="install-freeode"></A>
  <h2>Installing Freeode</h2>
  <p>
    Get the latest source <strong>tar.gz</strong> package
    (for example <strong>freeode-0.3.0.tar.gz</strong>) from the
    <A href="https://developer.berlios.de/project/showfiles.php?group_id=5610">download</A>
    section and and extract the contents.
    Then run the setup script (<strong>python setup.py install</strong>).
    Ready.
  </p>
  <p>
    You can also create binary packages (<strong>rpm deb? exe</strong>) with this script;
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
