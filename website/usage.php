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
    <li>Usage</li>
    <li><A href="usage.php#top">Top</A></li>
    <li><A href="usage.php#run_compiler">Compiler</A></li>
    <!--<li><A href="usage.php#options">Compiler Options</A></li>-->
    <li><A href="usage.php#run_generated_program">Generated Program</A></li>
  </ul>
</div>


<div id="contents">
  <h1>Usage</h1>

  <a name="run_compiler"></a>
  <h2>Running the Compiler</h2>
  <p>
    The compiler is a script named <strong>simlc</strong>.
    It reads a program file in the SIML language, and writes
    a program file in the python language. Diagnostic output is
    printed to the console. General usage is:
  </p>
  <p>
    simlc &#060;input file name&#062; [&#060;options&#062;]
  </p>
  <p>
    When no options are given, the generated python program will have
    the same base name as the input program, but with the extension
    changed to ".py".
    Specifically the command below will produce an executable python
    program with the name "bioreactor_simple.py".
  </p>
  <div id="code">
    <pre>
$> simlc bioreactor_simple.siml
    </pre>
  </div>

  <a name="options"></a>
  <h3>Options</h3>
  <ul>
    <li>
      <strong>-h, --help</strong>
      <p>Print extensive help message and exit.</p>
    </li>
    <li>
      <strong>--version</strong>
      <p>Print program's version number and exit.</p>
    </li>
    <li>
      <strong>-o &#060;output_file>, --outfile=&#060;output_file></strong>
      <p>Explicitly specify the name of the output file.</p>
    </li>
    <li>
      <strong>-r &#060;number>, --run=&#060;number></strong>
      <p>Run the generated simulation program after compiling.</p>
      <p>

        The &#060;number> specifies which of the program's
        simulation processes is run. The number counts from the top
        of the simulation program.
        The special value <strong>"all"</strong> means:
        run all simulation processes.
      </p>
    </li>
  </ul>


  <a name="run_generated_program"></a>
  <h2>Running the Generated Program</h2>
  <p>
    When the generated program is started with no options, all simulations
    in the program are run. The program also has some command line options.
  </p>

  <h3>Options</h3>
  <ul>
    <li>
      <strong>-h, --help</strong>
      <p>Print extensive help message and exit.</p>
    </li>
    <li>
      <strong>-l, --list</strong>
      <p>List the available simulations and exit.</p>
    </li>
    <li>
      <strong>-r &#060;number>, --run=&#060;number></strong>
      <p>Run the generated simulation program after compiling.</p>
      <p>

        The &#060;number> specifies which of the program's
        simulation processes is run. The number counts from the top
        of the simulation program.
        The special value <strong>"all"</strong> means:
        run all simulation processes, which is equivalent to giving no options.
      </p>
    </li>
    <li>
      <strong>--prepend-newline</strong>
      <p>
        Prepend the output with one newline.
        Only usefull when the program is started from the compiler.
      </p>
    </li>
  </ul>


</div>


<!--footer with required berlios image and copyright notice-->
<?php if( file_exists("footer.html") ){ include("footer.html"); } ?>

</body>
</html>
