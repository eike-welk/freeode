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

<!--<div id="info">
  <h2>info-Box</h2>
  <p>Some info text</p>
</div>-->

<div id="contents">
  <h1>The Freeode Project</h1>

  <h2>Intro</h2>
  <p>
    The Freeode project provides a simple programming language, and a
    matching compiler, to numerically solve differential equations. The compiler
    produces source code in the interpreted language
    <A href="http://www.python.org/">Python</A>,
    that performs the numerical computations.
    Both dynamic and steady state simulations can be done.
    The
    <A href="http://www.scipy.org/">SciPy</A>
    and
    <A href="http://numpy.scipy.org/">NumP</A>
    libraries are used for the numerical computations. Currently only
   <abbr TITLE="ordinary differential equations">ODE</abbr>
    can be solved.
  </p>
  <p>
    The generated Python code can be used with a minimal main program, or in an
    interactive Python session. Especially can the generated Python objects be used
    as building blocks of more complex programs. The programmer is freed
    from the relatively mechanical task of implementing the simulation function, and
    can concentrate on the higher level aspects of the problem.
  </p>

  <h2>Why Python</h2>
  <p>
    The free SciPy libraries turn the Python language into a prototyping environment
    for numerical algorithms, quite similar to the commercial language Matlab.
    There are several other free numerical prototyping languages; examples are Octave and Scilab.
    Python however is a general-purpose programming language with a rich standard library.
    Most notably here, is Python's powerfull string processing and file I/O.
  </p>

<!--    With a Python
    <abbr title="integrated development environment">IDE</abbr>
    like Eric one can have both at
    once, very much like the Matlab
    <abbr title="integrated development environment">IDE</abbr>
    (which is for the commercial language Matlab).-->

  <h2>License</h2>
  <p>
    The compiler is licensed under the
    <abbr title="GNU General Public License">GPL</abbr>.
    The runtime libraries are licensed under the
    <abbr title="GNU Library General Public License">LGPL</abbr> so they can be linked to commercial
    applications. The generated program can offcourse be licensed under any license you whish.
  </p>


  <h2>Incomplete example session</h2>
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

  <h3>The Differential Equations</h3>
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
          <span style="font-style: italic;color: #808080;">Growth speed</span>
        </td>
      </tr>
    </tbody>
  </table>

  <br>
  <p>
    Initial values and the values of the parameters have been omitted for brevity.
  </p>


  <h3>Equivalent Siml code</h3>
  <div id="code">
    <pre>
<span style="color: #0000ff;">MODEL</span><span style="color: #000000;"> BioReactor</span>
<span style="color: #000000;">    </span><span style="color: #0000ff;">PARAMETER</span><span style="color: #000000;"> </span><span style="font-style: italic;color: #808080;">#Values that stay constant</span>
<span style="color: #000000;">        mu_max; Ks; Yxs; Sf;</span>
<span style="color: #000000;">    </span><span style="color: #0000ff;">VARIABLE</span><span style="color: #000000;"> </span><span style="font-style: italic;color: #808080;"> #Values that change</span>
<span style="color: #000000;">        mu; X; S;</span>
<span style="color: #000000;">    </span><span style="color: #0000ff;">EQUATION</span><span style="color: #000000;"> </span><span style="font-style: italic;color: #808080;"> #Differential and algebraic equations</span>
<span style="color: #000000;">        mu </span><span style="color: #ff00ff;">:=</span><span style="color: #000000;"> mu_max </span><span style="color: #ff00ff;">*</span><span style="color: #000000;"> S</span><span style="color: #ff00ff;">/(</span><span style="color: #000000;">S</span><span style="color: #ff00ff;">+</span><span style="color: #000000;">Ks</span><span style="color: #ff00ff;">)</span><span style="color: #000000;">; </span><span style="font-style: italic;color: #808080;">#growth speed</span>
<span style="color: #000000;">        </span><span style="color: #ff00ff;">$</span><span style="color: #000000;">X </span><span style="color: #ff00ff;">:=</span><span style="color: #000000;"> mu</span><span style="color: #ff00ff;">*</span><span style="color: #000000;">X;              </span><span style="font-style: italic;color: #808080;">#change of biomass concentration</span>
<span style="color: #000000;">        </span><span style="color: #ff00ff;">$</span><span style="color: #000000;">S </span><span style="color: #ff00ff;">:=</span><span style="color: #000000;"> </span><span style="color: #ff00ff;">-</span><span style="color: #0000ff;">1</span><span style="color: #ff00ff;">/</span><span style="color: #000000;">Yxs</span><span style="color: #ff00ff;">*</span><span style="color: #000000;">mu</span><span style="color: #ff00ff;">*</span><span style="color: #000000;">X;       </span><span style="font-style: italic;color: #808080;">#change of sugar concentration</span>
<span style="color: #0000ff;">END</span>

<span style="color: #0000ff;">PROCESS</span> Batch
    <span style="font-style: italic;color: #808080;">#Omissions</span>
<span style="color: #0000ff;">END</span>
    </pre>
  </div>

  <p>
    Again the initial values and the values of the parameters have been omitted for brevity.
  </p>


  <h3>The generated Python code</h3>
  <div id="code">
    <pre>
<span style="font-weight: bold;color: #000000;">class</span><span style="color: #000000;"> Batch</span><span style="color: #ff00ff;">(</span><span style="color: #000000;">SimulatorBase</span><span style="color: #ff00ff;">):</span>
<span style="color: #000000;">    </span><span style="font-style: italic;color: #808080;">#Omissions</span>
<span style="color: #000000;">    </span>
<span style="color: #000000;">    </span><span style="font-weight: bold;color: #000000;">def</span><span style="color: #000000;"> _diffStateT</span><span style="color: #ff00ff;">(</span><span style="color: #008000;">self</span><span style="color: #000000;">, y, time</span><span style="color: #ff00ff;">):</span>

<span style="color: #000000;">        </span><span style="font-style: italic;color: #808080;">#Dissect the state vector into individual, local state variables.</span>
<span style="color: #000000;">        v_r_X </span><span style="color: #ff00ff;">=</span><span style="color: #000000;"> y</span><span style="color: #ff00ff;">[</span><span style="color: #0000ff;">0</span><span style="color: #ff00ff;">]</span>
<span style="color: #000000;">        v_r_S </span><span style="color: #ff00ff;">=</span><span style="color: #000000;"> y</span><span style="color: #ff00ff;">[</span><span style="color: #0000ff;">1</span><span style="color: #ff00ff;">]</span>

<span style="color: #000000;">        </span><span style="font-style: italic;color: #808080;">#Create the return vector (the time derivatives dy/dt).</span>
<span style="color: #000000;">        y_t </span><span style="color: #ff00ff;">=</span><span style="color: #000000;"> zeros</span><span style="color: #ff00ff;">(</span><span style="color: #0000ff;">2</span><span style="color: #000000;">, Float</span><span style="color: #ff00ff;">)</span>

<span style="color: #000000;">        </span><span style="font-style: italic;color: #808080;">#Compute the algebraic variables.</span>
<span style="color: #000000;">        v_r_mu </span><span style="color: #ff00ff;">=</span><span style="color: #000000;"> </span><span style="color: #008000;">self</span><span style="color: #000000;">.p_mu_max </span><span style="color: #ff00ff;">*</span><span style="color: #000000;"> v_r_S </span><span style="color: #ff00ff;">/</span><span style="color: #000000;"> </span><span style="color: #ff00ff;">(</span><span style="color: #000000;">v_r_S </span><span style="color: #ff00ff;">+</span><span style="color: #000000;"> </span><span style="color: #008000;">self</span><span style="color: #000000;">.p_Ks</span><span style="color: #ff00ff;">)</span>
<span style="color: #000000;">        </span><span style="font-style: italic;color: #808080;">#Compute the state variables. (Really the time derivatives.)</span>
<span style="color: #000000;">        y_t</span><span style="color: #ff00ff;">[</span><span style="color: #0000ff;">0</span><span style="color: #ff00ff;">]</span><span style="color: #000000;"> </span><span style="color: #ff00ff;">=</span><span style="color: #000000;"> v_r_mu </span><span style="color: #ff00ff;">*</span><span style="color: #000000;"> v_r_X </span><span style="font-style: italic;color: #808080;"># = d r.X /dt</span>
<span style="color: #000000;">        y_t</span><span style="color: #ff00ff;">[</span><span style="color: #0000ff;">1</span><span style="color: #ff00ff;">]</span><span style="color: #000000;"> </span><span style="color: #ff00ff;">=</span><span style="color: #000000;"> </span><span style="color: #ff00ff;">-</span><span style="color: #0000ff;">1</span><span style="color: #000000;"> </span><span style="color: #ff00ff;">/</span><span style="color: #000000;"> </span><span style="color: #008000;">self</span><span style="color: #000000;">.p_Yxs </span><span style="color: #ff00ff;">*</span><span style="color: #000000;"> v_r_mu </span><span style="color: #ff00ff;">*</span><span style="color: #000000;"> v_r_X </span><span style="font-style: italic;color: #808080;"># = d r.S /dt</span>

<span style="color: #000000;">        </span><span style="font-weight: bold;color: #000000;">return</span><span style="color: #000000;"> y_t</span>
    </pre>
  </div>

  <p>
    Much of the generated Python code has been omitted. Only the simulation function is shown.
    The omitted parts of the code are responsible for setting up the simulation object,
    performing the simulation, and comfortable access to the results of the simulation.
  </p>
  <p>
    Note that the algebraic variables are not part of the state vector (as usual).
    They have to be computed for a second time to access them as results too.
    Here there is a single algebraic variable: µ = mu = v_r_mu.
  </p>


  <h3>The commands</h3>

  <p>
    These are the commands for a very simple session with an interactive Python interpreter.
  </p>

  <div id="code">
    <pre>
$> kwrite bioreactor_simple.siml     <span style="font-style: italic;color: #808080;">#Edit Siml file</span>
$> siml bioreactor_simple.siml       <span style="font-style: italic;color: #808080;">#Run compiler</span>
Generated process: Batch

$> python                            <span style="font-style: italic;color: #808080;">Start Python interpreter</span>
Python 2.4  <span style="font-style: italic;color: #808080;">(Most of Python's startup message omitted.)</span>
>>> execfile('bioreactor_simple.py') <span style="font-style: italic;color: #808080;">Load generated file into Python</span>
>>> s = Batch()                      <span style="font-style: italic;color: #808080;">Create simulation object</span>
>>> s.simulateDynamic()              <span style="font-style: italic;color: #808080;">Perform simulation</span>
>>> s.graph('r.S r.X')               <span style="font-style: italic;color: #808080;">Show results</span>
    </pre>
  </div>

  <p>This opens a window with the following graph:</p>

  <img src="bioreactor_simple - r.S r.X.png" alt="Graph of X and S, produced by the  bioreactor_simple.siml program" width="640" height="450" align="left" border="0">

</div>


<!--footer with the required berlios image-->
<?php if( file_exists("footer.html") ){ include("footer.html"); } ?>

</body>
</html>
