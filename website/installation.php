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
	<A href="http://matplotlib.sourceforge.net/">website</A> also contains some
	<A href="http://matplotlib.sourceforge.net/users/installing.html">installation instructions</A>.
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
    Freeode is distributed in several different formats: Files in *.rpm and 
    *.exe formats can usually be installed by clicking on them
    (in RPM based Linux and Windows respectively). Software installed from these 
    files can usually be easily removed from the computer, by the operating 
    system's software management program.
    To use *.tar.gz and *.zip files you need to enter some 
    textual commands to perform the installation. The textual commands are quite 
    powerful. You can create *.rpm and *.exe  files from the *.tar.gz and *.zip 
    files. 
  </p>
  <p>
    All files are available from Freeode's
    <A href="https://developer.berlios.de/project/showfiles.php?group_id=5610">download area</A>
    .
  </p>

  <h4>Linux</h4>
  <p>On RPM based Distributions (Suse, Red Hat, Mandriva, ...) 
  <A href="https://developer.berlios.de/project/showfiles.php?group_id=5610">download</A>
  the latest <strong>*.rpm</strong> file
  and click on it. The software management program (the package manager) should 
  pop up and install the software, after asking you for the root password. 
  To remove the package go to the package manager's list of installed 
  software, search for a package named "freeode", and remove it.</p>
  
  <p>If you can't (or d'don't want to) use RPM packages, download the latest
  <strong>*.tar.gz</strong> file, open a shell window and type the following 
  commands:</p>

  <div id="code">
    <pre>
> cd **where you put the downloaded *.tar.gz file**
> tar xvf freeode-0.4.0.tar.gz     #extract package contents
> cd freeode-0.4.0/                #enter extracted directory
> su                               #become root
Password:
> python setup.py install          #run installation script
> rm -rf build                     #remove the intermediate files
> exit                             #give back root privileges 
    </pre>
  </div>
  
  <p>The command to create RPM files, if the supplied *.rpm file does not work 
  on your system is:</p>
  <div id="code">
    <pre>
> python setup.py bdist_rpm       #create RPM in directory dist/ 
    </pre>
  </div>
  
  <h4>Windows</h4>
  <p>
	  <small><b>
	  Someone please try out the Windows installer, and let me know if it really 
	  works! Does un-installing work? The Windows installer has never been tested, 
	  because Freeode's development happens entirely on Linux. Building Windows 
	  installers is a built in feature of Python, which is even available on Linux.
	  </b></small>
  </p>
  
  <p>On Windows download the *.exe file and click on it. An installer
  should pop up and install the software. You possibly need to enter the 
  administrator password. Windows has a feature to remove software in the 
  control panel (in Windows Vista it is  called "Programs and Features").</p>
  
  <p>For a text based installation do the following steps:
  <ul>
    <li>
      <A href="https://developer.berlios.de/project/showfiles.php?group_id=5610">Download</A>
      the latest (<strong>*zip</strong>) file.
    </li>
    <li>
      Extract the contents of the package.
    </li>
    <li>Open a DOS box.</li>
    <li>Change to the directory to where you downloaded the package.</li>
    <li>
      Run the installation script by typing: (You might need administrator 
      privileges.)
	  <div id="code">
	    <pre>
 python setup.py install 
        </pre>
      </div>
    </li>
    <li>
      If you want to build a Windows installer, so that you can easily remove 
      the software again, type the following command:
      <div id="code">
        <pre>
 python setup.py bdist_wininst
        </pre>
      </div>
    </li>
 </ul>
</div>


<!--footer with the required berlios image-->
<?php if( file_exists("footer.html") ){ include("footer.html"); } ?></body>
</html>
