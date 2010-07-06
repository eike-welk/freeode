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
    <strong>simlc &lt;input file name&#062; [&lt;options&gt;]</strong>
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
$&gt; simlc bioreactor_simple.siml 
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
      <strong>-o &lt;output_file&gt;, --outfile=&lt;output_file&gt;</strong>
      <p>Explicitly specify the name of the output file.</p>
    </li>
    <li>
      <strong>-r &lt;number&gt;, --run=&lt;number&gt;</strong>
      <p>Run the generated simulation program after compiling.</p>
      <p>

        The &lt;number&gt; specifies which of the program's
        simulation processes is run. The number counts from the top
        of the simulation program.
        The special value <strong>"all"</strong> means:
        run all simulation processes.
      </p>
    </li>
    <li>
      <strong>--no-graphs</strong>
      <p> Do not show any graph windows if running the simulation,  
      in spite of calls to the <strong>graph</strong> functions. </p>
    </li>
    <li>
      <strong>--debug-areas=&lt;area1,area2,...&gt;</strong>
      <p>Specify debug areas to control printing of debug information, and the 
      output of the <strong>printc</strong> function. 
      This option is passed on to the simulation, if it is run.</p>
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
      <strong>-r &lt;number&gt;, --run=&lt;number&gt;</strong>
      <p>Run the generated simulation program after compiling.</p>
      <p>

        The &lt;number&gt; specifies which of the program's
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
        Only useful when the program is started from the compiler.
      </p>
    </li>
    <li>
      <strong>--no-graphs</strong>
      <p> Do not show any graph windows in spite of calls to the 
      <strong>graph</strong> functions. </p>
    </li>
    <li>
      <strong>--debug-areas=&lt;area1,area2,...&gt;</strong>
      <p>Specify debug areas to control the output of the 
      <strong>print</strong> function.</p>
    </li>
  </ul>


</div>


<!--footer with required berlios image and copyright notice-->
<?php if( file_exists("footer.html") ){ include("footer.html"); } ?>

</body>
</html>
