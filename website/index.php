<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">
<html>

<head>
  <title>SIML simulation language</title>
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


<!--Navigation on the page-->
<div id="navigation_page">
  <ul>
    <li>The Freeode Project</li>
    <li><a href="index.php#top">Top</a></li>
    <li><a href="index.php#why_python">Why Python</a></li>
    <li><a href="index.php#license">License</a></li>
    <li><a href="index.php#example_session">Example Session</a></li>
    <li><a href="index.php#differential_equations">Differential Equations</a></li>
    <li><a href="index.php#siml_program">SIML Program</a></li>
    <li><a href="index.php#generated_python_code">Generated Python Code</a></li>
    <li><a href="index.php#shell_commands">Shell Commands</a></li>
  </ul>
</div>


<!--really; this is the links page-->
<div id="navigation_page">
  <ul>
    <li>Python</li>
    <li><A href="http://www.python.org/">Python project page</A></li>
    <li><A href="http://www.scipy.org/">SciPy project page</A></li>
    <li><A href="http://docs.python.org/tut/tut.html">Official Python Tutorial</A></li>
    <li><A href="http://diveintopython.org/">Alternative Python tutorial</A></li>
    <li><A href="http://www.amazon.com/gp/product/3540294155/">Python Scripting for Computational Science (Book)</A></li>
  </ul>
</div>


<!--<div id="info">
  <h2>info-Box</h2>
  <p>Some info text</p>
</div>-->


<div id="contents">
  <A name="top"></A>
  <h1>The Freeode Project</h1>

  <p>
    The Freeode project provides a simple programming language,
    to numerically solve differential equations.
    The compiler produces source code in the interpreted language
    <A href="http://www.python.org/">Python</A>,
    that performs the numerical computations.
    Both dynamic and steady state simulations can be done.
    The
    <A href="http://www.scipy.org/">SciPy</A>
    and
    <A href="http://numpy.scipy.org/">NumPy</A>
    libraries are used for the numerical computations. Currently only
    <abbr TITLE="ordinary differential equations">ODE</abbr>
    can be solved.
  </p>
  <p>
    The generated Python code can be used as a stand-alone program, or in an
    interactive Python session. Especially can the generated Python objects be used
    as building blocks of more complex programs. The programmer is freed
    from the relatively mechanical task of implementing the simulation function, and
    can concentrate on the higher level aspects of the problem.
  </p>
  <p>
    Python promises to be highly platform independent.
    Therefore everything should work on Windows exactly as it works on Linux.
  </p>


  <A name="why_python"></A>
  <h2>Why Python</h2>
  <p>
    The free SciPy and NumPy libraries turn the Python language into
    a prototyping environment for numerical algorithms,
    quite similar to the commercial language
    <A href="http://www.mathworks.com/">Matlab</A>.
    There are several other free numerical prototyping languages; examples are
    <A href="http://www.gnu.org/software/octave/">Octave</A> and
    <A href="http://www.scilab.org/">Scilab</A>.
    Python however is a general-purpose programming language with a rich standard library.
    Most notably here, is Python's powerfull string processing and file I/O.
  </p>

<!--    With a Python
    <abbr title="integrated development environment">IDE</abbr>
    like Eric one can have both at
    once, very much like the Matlab
    <abbr title="integrated development environment">IDE</abbr>
    (which is for the commercial language Matlab).-->


  <A name="license"></A>
  <h2>License</h2>
  <p>
    The compiler is licensed under the
    <abbr title="GNU General Public License">GPL</abbr>.
    The runtime libraries are licensed under the
    <abbr title="GNU Library General Public License">LGPL</abbr> so they can be linked to commercial
    applications. The generated program can off course be licensed under any license you wish.
  </p>


  <!-- ================ Example Session =======================================-->
  <A name="example_session"></A>
  <h2>Example Session</h2>
  <p>
    This rough example should give a first impression of the usage
    of the compiler and of the generated program.
    Also it should show what code the compiler emits.
  </p>
  <p>
    A simple biological reactor should be simulated. The simulation has two
    state variables:
    <strong>X</strong> the concentration of biomass, and
    <strong>S</strong> the concentration of sugar.
    The growth speed <strong>&#181;</strong> is an algebraic variable.
  </p>


  <!-- ================ Differential Equations =======================================-->
  <A name="differential_equations"></A>
  <h3>Differential Equations</h3>
  <table>
    <tbody>
      <tr>
        <td>dX/dt = &#181;*X</td>
        <td>
          &nbsp;&nbsp;
          <span style="font-style: italic;color: #808080;">Change of biomass concentration</span>
        </td>
      </tr>
      <tr>
        <td>dS/dt = -1/Y<sub>xs</sub>*&#181;*X</td>
        <td>
          &nbsp;&nbsp;
          <span style="font-style: italic;color: #808080;">Change of sugar concentration</span>
        </td>
      </tr>
      <tr>
        <td>with:</td>
        <td></td>
      </tr>
      <tr>
        <td>&#181; = &#181;<sub>max</sub> * S/(S+K<sub>s</sub>)</td>
        <td>
          &nbsp;&nbsp;
          <span style="font-style: italic;color: #808080;">Growth speed of biomass</span>
        </td>
      </tr>
    </tbody>
  </table>

  <br>
  <p>
    Initial values and the values of the parameters have been omitted for brevity.
  </p>


  <!-- ================ Siml code =======================================-->
  <A name="siml_program"></A>
  <h3>SIML Program</h3>
  <div id="code">
    <pre>
<span style='color: #888786'><i>#Biological reactor with no inflow or outfow</i></span>
<span style='color: #141312'><b>class</b> Batch:</span>
<span style='color: #141312'>    </span><span style='color: #888786'><i>#Define values that stay constant during the simulation.</i></span>
<span style='color: #141312'>    <b>data</b> mu_max, Ks, Yxs: Float <b>param</b></span>
<span style='color: #141312'>    </span><span style='color: #888786'><i>#Define values that change during the simulation.</i></span>
<span style='color: #141312'>    <b>data</b> mu, X, S: Float</span>

<span style='color: #141312'>    </span><span style='color: #888786'><i>#Initialize the simulation.</i></span>
<span style='color: #141312'>    <b>func</b> </span><span style='color: #0095ff'><b>initialize</b></span><span style='color: #141312'>(</span><span style='color: #006e28'>this</span><span style='color: #141312'>):</span>
<span style='color: #141312'>        </span><span style='color: #888786'><i>#Specify options for the simulation algorithm.</i></span>
<span style='color: #141312'>        solution_parameters(duration=</span><span style='color: #b08000'>20</span><span style='color: #141312'>, reporting_interval=</span><span style='color: #b08000'>0.1</span><span style='color: #141312'>)</span>
<span style='color: #141312'>        </span><span style='color: #888786'><i>#Give values to the parameters</i></span>
<span style='color: #141312'>        mu_max = </span><span style='color: #b08000'>0.32</span><span style='color: #141312'>; </span><span style='color: #888786'><i>#max growth speed</i></span>
<span style='color: #141312'>        Ks     = </span><span style='color: #b08000'>0.01</span><span style='color: #141312'>; </span><span style='color: #888786'><i>#at this sugar concentration growth speed is 0.5*mu_max</i></span>
<span style='color: #141312'>        Yxs    = </span><span style='color: #b08000'>0.5</span><span style='color: #141312'>;  </span><span style='color: #888786'><i>#one g sugar gives this much biomass</i></span>
<span style='color: #141312'>        </span><span style='color: #888786'><i>#Give initial values to the state variables.</i></span>
<span style='color: #141312'>        X      = </span><span style='color: #b08000'>0.1</span><span style='color: #141312'>;  </span><span style='color: #888786'><i>#initial biomass concentration</i></span>
<span style='color: #141312'>        S      = </span><span style='color: #b08000'>20</span><span style='color: #141312'>;   </span><span style='color: #888786'><i>#initial sugar concentration</i></span>


<span style='color: #141312'>    </span><span style='color: #888786'><i>#compute dynamic behaviour - the system's 'equations'</i></span>
<span style='color: #141312'>    <b>func</b> </span><span style='color: #0095ff'><b>dynamic</b></span><span style='color: #141312'>(</span><span style='color: #006e28'>this</span><span style='color: #141312'>):</span>
<span style='color: #141312'>        mu = mu_max * S/(S+Ks); </span><span style='color: #888786'><i>#growth speed (of biomass)</i></span>
<span style='color: #141312'>        $X = mu*X;              </span><span style='color: #888786'><i>#change of biomass concentration</i></span>
<span style='color: #141312'>        $S = -</span><span style='color: #b08000'>1</span><span style='color: #141312'>/Yxs*mu*X;       </span><span style='color: #888786'><i>#change of sugar concentration</i></span>


<span style='color: #141312'>    </span><span style='color: #888786'><i>#show results</i></span>
<span style='color: #141312'>    <b>func</b> </span><span style='color: #0095ff'><b>final</b></span><span style='color: #141312'>(</span><span style='color: #006e28'>this</span><span style='color: #141312'>):</span>
<span style='color: #141312'>        </span><span style='color: #0057ae'>graph</span><span style='color: #141312'>(mu, X, S);</span>


<span style='color: #141312'><b>compile</b> Batch</span>
    </pre>
  </div>

  <p>
    This is a complete SIML program to to solve the system of differential equations.
    The differential equations are in the <strong>dynamic</strong> function.
    The <strong>init</strong> function is invoked once at the beginning of the simulation,
    the <strong>final</strong> function is invoked at the end.
  </p>
  <p>
    The source distribution contains a syntax coloring file, for editors based on the
    <A href="http://kate-editor.org/">Katepart</A>.
    Therfore the editors Kate and Kwrite (and Kdevelop) can show SIML code colored like the
    example above. (The HTML of both code examples was generated by the Kate editor's HTML
    export feature.)
  </p>

  <!-- ================ Python code =======================================-->
  <A name="generated_python_code"></A>
  <h3>Generated Python Code</h3>
  <div id="code">
    <pre>
<span style="color: #000000;">    def dynamic</span><span style="color: #ff00ff;">(</span><span style="color: #008000;">self</span><span style="color: #000000;">, time, state, returnAlgVars</span><span style="color: #ff00ff;">=</span><span style="color: #008000;">False</span><span style="color: #ff00ff;">)</span><span style="color: #000000;">:</span>
<span style="font-style: italic;color: #808080;">        '''</span>
<span style="font-style: italic;color: #808080;">        Compute time derivative of state variables.</span>
<span style="font-style: italic;color: #808080;">        This function will be called by the solver repeatedly.</span>
<span style="font-style: italic;color: #808080;">        '''</span>
<span style="color: #000000;">        </span><span style="font-style: italic;color: #808080;">#take the state variables out of the state vector</span>
<span style="color: #000000;">        v_S </span><span style="color: #ff00ff;">=</span><span style="color: #000000;"> state[</span><span style="color: #0000ff;">0</span><span style="color: #000000;">]</span>
<span style="color: #000000;">        v_X </span><span style="color: #ff00ff;">=</span><span style="color: #000000;"> state[</span><span style="color: #0000ff;">1</span><span style="color: #000000;">]</span>
<span style="color: #000000;">        </span><span style="font-style: italic;color: #808080;">#do computations</span>
<span style="color: #000000;">        v_mu </span><span style="color: #ff00ff;">=</span><span style="color: #000000;"> </span><span style="color: #008000;">self</span><span style="color: #000000;">.p_mu_max</span><span style="color: #ff00ff;">*</span><span style="color: #000000;">v_S</span><span style="color: #ff00ff;">/(</span><span style="color: #000000;">v_S </span><span style="color: #ff00ff;">+</span><span style="color: #000000;"> </span><span style="color: #008000;">self</span><span style="color: #000000;">.p_Ks</span><span style="color: #ff00ff;">)</span>
<span style="color: #000000;">        v_X_dt </span><span style="color: #ff00ff;">=</span><span style="color: #000000;"> v_mu</span><span style="color: #ff00ff;">*</span><span style="color: #000000;">v_X</span>
<span style="color: #000000;">        v_S_dt </span><span style="color: #ff00ff;">=</span><span style="color: #000000;">  </span><span style="color: #ff00ff;">-</span><span style="color: #800080;">1.0</span><span style="color: #ff00ff;">/</span><span style="color: #008000;">self</span><span style="color: #000000;">.p_Yxs</span><span style="color: #ff00ff;">*</span><span style="color: #000000;">v_mu</span><span style="color: #ff00ff;">*</span><span style="color: #000000;">v_X</span>

<span style="color: #000000;">        if returnAlgVars:</span>
<span style="color: #000000;">            </span><span style="font-style: italic;color: #808080;">#put algebraic variables into array</span>
<span style="color: #000000;">            algVars </span><span style="color: #ff00ff;">=</span><span style="color: #000000;"> array</span><span style="color: #ff00ff;">(</span><span style="color: #000000;">[v_mu, ], </span><span style="color: #ff0000;">'float64'</span><span style="color: #ff00ff;">)</span>
<span style="color: #000000;">            return algVars</span>
<span style="color: #000000;">        else:</span>
<span style="color: #000000;">            </span><span style="font-style: italic;color: #808080;">#assemble the time derivatives into the return vector</span>
<span style="color: #000000;">            stateDt </span><span style="color: #ff00ff;">=</span><span style="color: #000000;"> array</span><span style="color: #ff00ff;">(</span><span style="color: #000000;">[v_S_dt, v_X_dt, ], </span><span style="color: #ff0000;">'float64'</span><span style="color: #ff00ff;">)</span>
<span style="color: #000000;">            return stateDt</span>
    </pre>
  </div>
  <p>
    This is the generated simulation function. The compiler emits code with comments,
    so that humans have a chance to understand it.
    Much of the generated Python code has been omitted.
    The omitted parts initialize the simulation object,
    and show the results.
  </p>
  <p>
    The compiler does what a human programmer would also (have to) do.
    The problem dependent part is only three lines (below the comment:
    <em>do computations</em>).
    The rest of the code takes numbers out of arrays, or puts them into arrays.
    When the length of the state vector changes, a human programmer would
    have to update the array indices in the whole program.
    A tedious and error prone work.
  </p>
  <p>
    The simulation function can return either derivatives of the state variables,
    or algebraic variables.
    The algebraic variables have to be computed separately,
    because the solver algorithm does only see the derivatives.
  </p>


  <!-- ================ Shell Commands =======================================-->
  <A name="shell_commands"></A>
  <h3>Shell Commands</h3>

  <p>
    These are the (bash) commands to edit the program, compile it, and run it.
  </p>
  <div id="code">
    <pre>
$> kwrite bioreactor_simple.siml &#038;  <span style="font-style: italic;color: #808080;">#Edit Siml file</span>
$> simlc bioreactor_simple.siml     <span style="font-style: italic;color: #808080;">#Run compiler</span>
$> ./bioreactor_simple.py           <span style="font-style: italic;color: #808080;">#Run generated program</span>
    </pre>
  </div>

  <p>
  The compiler can also run the generated Program.
  This is useful for the development of simulation programs.
  </p>
  <div id="code">
    <pre>
$> kwrite bioreactor_simple.siml &#038;     <span style="font-style: italic;color: #808080;">#Edit Siml file</span>
$> simlc bioreactor_simple.siml -r all <span style="font-style: italic;color: #808080;">#Run compiler</span>
    </pre>
  </div>

  <p>After the commands have been executed, a window opens, that shows the simulation results:</p>

  <img src="bioreactor_simple - r.S r.X.png" alt="Graph of X, S and mu, produced by the bioreactor_simple.siml program" width="640" height="514" align="left" border="0">

</div>


<!--footer with the required berlios image-->
<?php if( file_exists("footer.html") ){ include("footer.html"); } ?>

</body>
</html>
