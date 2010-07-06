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
  <h1>Links</h1>

  <h2>Python</h2>
  <ul>
    <li><A href="http://www.python.org/">Python project page</A></li>
    <li><A href="http://www.scipy.org/">SciPy project page</A></li>
    <li><A href="http://docs.python.org/tut/tut.html">Official Python Tutorial</A></li>
    <li><A href="http://diveintopython.org/">Dive Into Python</A>
      <p>Alternative Python tutorial</p>
    </li>
    <li><A href="http://www.amazon.com/Python-Scripting-Computational-Science-Engineering/dp/3540739157">
          Python Scripting for Computational Science</A>
      <p>
        Book. Introduction to Python and to numerical libraries for
        scientists and engineers. A little dated but still very useful.
      </p>
    </li>
  </ul>

  <h2>
    Text Editors and
    <abbr title="Integrated Development Environment">IDE</abbr>s
  </h2>
  <ul>
    <li><A href="http://kate-editor.org/">Kate</A>
      <p>
        Sophisticated editor with flexible syntax coloring.
        Syntax coloring for the SIML language is possible;
        a highlighting XML-file is in the Freeode sources.
        Also useful for small scale Python programming.
      </p>
    </li>
    <li><A href="http://eric-ide.python-projects.org/index.html">Eric</A></li>
    <p>
      Simple Python IDE. Favors experimention; very useful for applications
      using NumPy or SciPy. No flexible syntax coloring.
    </p>
    <li><A href="http://pydev.org/">PyDev</A>
      <p>
        Extension for Eclipse. Has the best code completion of the free
        Python IDEs I know. Fairly slow however.
      </p>
    </li>
    <!-- <li>http://sourceforge.net/projects/qme-dev/</li> -->
  </ul>

  <h2>Similar Projects</h2>
  <ul>
    <li><a href="http://www.warrenweckesser.net/vfgen/">VFGEN</a>
      <p>
        Differential equation is specified through XML.
        Can generate code for wide variety of solvers and other tools.
      </p>
    </li>
  </ul>

  <h2>Commercial Software</h2>
  <ul>
    <li><a href="http://www.psenterprise.com/gproms/">gPROMS</a>
      <p>
        Much more sophisticated than Freeode! It can solve ordinary and partial
        differential equations. In addition to differential equations, it can
        also simulate event based models that interact with the differential 
        equations. Newer versions have a graphical editor.
      </p>
      <p>
        The differential equation are modeled declaratively (as real equations), 
        Freeode in contrast is imperative. This is 
        quite elegant for writing the simulations and for code reuse. Debugging 
        however is more hard, and it can lead to numerical instabilities.
      </p>
    </li>
    <li><a href="http://www.modelica.org/">Modelica</a>
      <p>
        Modelica is a versatile language for simulating physical systems.
        Continuous models can be specified in declarative (equation based) or 
        imperative fashion. Event based models are also possible (IMHO). 
        However partial differential equations can not be solved.
      </p>  
      <p> 
        There are several free and commercial implementations available.
        Some commercial implementations have a graphical editor.
      </p>
    </li>
  </ul>



</div>


<!--footer with required berlios image and copyright notice-->
<?php if( file_exists("footer.html") ){ include("footer.html"); } ?>

</body>
</html>
