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
    <li>The SIML Language</li>
    <li><A href="language.php#top">Top</A></li>
    <li><A href="language.php#tutorial">Tutorial</A></li>
    <li><A href="language.php#syntax">Syntax</A></li>
  </ul>
</div>


<div id="contents">
  <a name="top"></a>
  <h1>The SIML Language</h1>

  <a name="tutorial"></a>
  <h2>Tutorial</h2>
  <p>To be done</p>

  <a name="syntax"></a>
  <h2>The Syntax</h2>
  <p>
    The syntax is roughly object orinented. A simulation consists
    of one or more class definitions.
  </p>

  <h3>class</h3>
  <div id="code">
    <pre>
class <em>class_name</em>(<em>base_class</em>):
    <em>#data members</em>

    <em>#member functions</em>
end
    </pre>
  </div>

  <p>
    The data attributes are defined first, then come the member functions.
  </p>
  <p>
    There are two base classes:
    <ul>
      <li><strong>process</strong>:
          A numerical experiment.
          Should contain models, initial values and parameters.
          Classes inheriting from process are compiled into simulation objects.
      </li>
      <li><strong>model</strong>:
          Building blocks of the processes. The equations should go here.
          Models can only exist as data attributes of processes.
      </li>
    </ul>
  </p>
</div>


<!--footer with the required berlios image-->
<?php if( file_exists("footer.html") ){ include("footer.html"); } ?>

</body>
</html>
