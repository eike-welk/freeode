<?xml version='1.0' encoding='ISO-8859-1' standalone='yes'?>
<tagfile>
  <compound kind="file">
    <name>main.cpp</name>
    <path>/home/eike/sim_lang/src/</path>
    <filename>main_8cpp</filename>
    <includes id="parser_8h" name="parser.h" local="yes" imported="no">parser.h</includes>
    <member kind="function">
      <type>int</type>
      <name>main</name>
      <anchor>a0</anchor>
      <arglist>()</arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>parser.cpp</name>
    <path>/home/eike/sim_lang/src/</path>
    <filename>parser_8cpp</filename>
    <includes id="parser_8h" name="parser.h" local="yes" imported="no">parser.h</includes>
    <includes id="siml__skip__grammar_8h" name="siml_skip_grammar.h" local="yes" imported="no">siml_skip_grammar.h</includes>
    <includes id="siml__name__grammar_8h" name="siml_name_grammar.h" local="yes" imported="no">siml_name_grammar.h</includes>
    <includes id="siml__model__grammar_8h" name="siml_model_grammar.h" local="yes" imported="no">siml_model_grammar.h</includes>
    <namespace>std</namespace>
    <namespace>boost::spirit</namespace>
    <member kind="define">
      <type>#define</type>
      <name>PHOENIX_LIMIT</name>
      <anchor>a0</anchor>
      <arglist></arglist>
    </member>
    <member kind="define">
      <type>#define</type>
      <name>BOOST_SPIRIT_CLOSURE_LIMIT</name>
      <anchor>a1</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>parser.h</name>
    <path>/home/eike/sim_lang/src/</path>
    <filename>parser_8h</filename>
  </compound>
  <compound kind="file">
    <name>siml_code_model.h</name>
    <path>/home/eike/sim_lang/src/</path>
    <filename>siml__code__model_8h</filename>
    <namespace>siml</namespace>
    <member kind="typedef">
      <type>std::vector&lt; parameter_descriptor &gt;</type>
      <name>parameter_table</name>
      <anchor>a0</anchor>
      <arglist></arglist>
    </member>
    <member kind="typedef">
      <type>std::vector&lt; variable_descriptor &gt;</type>
      <name>variable_table</name>
      <anchor>a1</anchor>
      <arglist></arglist>
    </member>
    <member kind="typedef">
      <type>std::vector&lt; equation_descriptor &gt;</type>
      <name>equation_table</name>
      <anchor>a2</anchor>
      <arglist></arglist>
    </member>
    <member kind="typedef">
      <type>std::vector&lt; model_descriptor &gt;</type>
      <name>model_table</name>
      <anchor>a3</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>siml_model_grammar.h</name>
    <path>/home/eike/sim_lang/src/</path>
    <filename>siml__model__grammar_8h</filename>
    <includes id="siml__code__model_8h" name="siml_code_model.h" local="yes" imported="no">siml_code_model.h</includes>
    <includes id="siml__name__grammar_8h" name="siml_name_grammar.h" local="yes" imported="no">siml_name_grammar.h</includes>
    <namespace>model_temp_store</namespace>
    <namespace>siml</namespace>
    <member kind="function">
      <type>void</type>
      <name>start_parameter</name>
      <anchor>a5</anchor>
      <arglist>(char const *, char const *)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>add_parameter</name>
      <anchor>a6</anchor>
      <arglist>(char const *first, char const *const last)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>start_variable</name>
      <anchor>a7</anchor>
      <arglist>(char const *, char const *)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>add_variable</name>
      <anchor>a8</anchor>
      <arglist>(char const *first, char const *const last)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>start_equation</name>
      <anchor>a9</anchor>
      <arglist>(char const *, char const *)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>add_algebraic_assignment</name>
      <anchor>a10</anchor>
      <arglist>(char const *first, char const *const last)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>add_derivative_assignment</name>
      <anchor>a11</anchor>
      <arglist>(char const *first, char const *const last)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>return_model</name>
      <anchor>a12</anchor>
      <arglist>(char const *, char const *const )</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>return_error</name>
      <anchor>a13</anchor>
      <arglist>(char const *, char const *const )</arglist>
    </member>
    <member kind="variable">
      <type>model_descriptor</type>
      <name>model</name>
      <anchor>a0</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>parameter_descriptor</type>
      <name>p_temp</name>
      <anchor>a1</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>variable_descriptor</type>
      <name>v_temp</name>
      <anchor>a2</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>equation_descriptor</type>
      <name>e_temp</name>
      <anchor>a3</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>string</type>
      <name>possible_error</name>
      <anchor>a4</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="file">
    <name>siml_name_grammar.h</name>
    <path>/home/eike/sim_lang/src/</path>
    <filename>siml__name__grammar_8h</filename>
    <namespace>siml</namespace>
  </compound>
  <compound kind="file">
    <name>siml_skip_grammar.h</name>
    <path>/home/eike/sim_lang/src/</path>
    <filename>siml__skip__grammar_8h</filename>
    <namespace>siml</namespace>
  </compound>
  <compound kind="class">
    <name>boost::spirit::grammar</name>
    <filename>classboost_1_1spirit_1_1grammar.html</filename>
  </compound>
  <compound kind="class">
    <name>boost::spirit::grammar</name>
    <filename>classboost_1_1spirit_1_1grammar.html</filename>
  </compound>
  <compound kind="class">
    <name>boost::spirit::grammar</name>
    <filename>classboost_1_1spirit_1_1grammar.html</filename>
  </compound>
  <compound kind="class">
    <name>Parser</name>
    <filename>classParser.html</filename>
    <member kind="function">
      <type></type>
      <name>Parser</name>
      <anchor>a0</anchor>
      <arglist>()</arglist>
    </member>
    <member kind="function">
      <type></type>
      <name>~Parser</name>
      <anchor>a1</anchor>
      <arglist>()</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>doParse</name>
      <anchor>a2</anchor>
      <arglist>()</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>doParseNumbers</name>
      <anchor>a3</anchor>
      <arglist>()</arglist>
    </member>
  </compound>
  <compound kind="dir">
    <name>/home/eike/sim_lang/</name>
    <path>/home/eike/sim_lang/</path>
    <filename>dir_000000.html</filename>
    <dir>/home/eike/sim_lang/src/</dir>
  </compound>
  <compound kind="dir">
    <name>/home/eike/sim_lang/src/</name>
    <path>/home/eike/sim_lang/src/</path>
    <filename>dir_000001.html</filename>
    <file>main.cpp</file>
    <file>parser.cpp</file>
    <file>parser.h</file>
    <file>siml_code_model.h</file>
    <file>siml_model_grammar.h</file>
    <file>siml_name_grammar.h</file>
    <file>siml_skip_grammar.h</file>
  </compound>
  <compound kind="namespace">
    <name>boost::spirit</name>
    <filename>namespaceboost_1_1spirit.html</filename>
  </compound>
  <compound kind="namespace">
    <name>model_temp_store</name>
    <filename>namespacemodel__temp__store.html</filename>
    <member kind="function">
      <type>void</type>
      <name>start_parameter</name>
      <anchor>a5</anchor>
      <arglist>(char const *, char const *)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>add_parameter</name>
      <anchor>a6</anchor>
      <arglist>(char const *first, char const *const last)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>start_variable</name>
      <anchor>a7</anchor>
      <arglist>(char const *, char const *)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>add_variable</name>
      <anchor>a8</anchor>
      <arglist>(char const *first, char const *const last)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>start_equation</name>
      <anchor>a9</anchor>
      <arglist>(char const *, char const *)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>add_algebraic_assignment</name>
      <anchor>a10</anchor>
      <arglist>(char const *first, char const *const last)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>add_derivative_assignment</name>
      <anchor>a11</anchor>
      <arglist>(char const *first, char const *const last)</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>return_model</name>
      <anchor>a12</anchor>
      <arglist>(char const *, char const *const )</arglist>
    </member>
    <member kind="function">
      <type>void</type>
      <name>return_error</name>
      <anchor>a13</anchor>
      <arglist>(char const *, char const *const )</arglist>
    </member>
    <member kind="variable">
      <type>model_descriptor</type>
      <name>model</name>
      <anchor>a0</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>parameter_descriptor</type>
      <name>p_temp</name>
      <anchor>a1</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>variable_descriptor</type>
      <name>v_temp</name>
      <anchor>a2</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>equation_descriptor</type>
      <name>e_temp</name>
      <anchor>a3</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>string</type>
      <name>possible_error</name>
      <anchor>a4</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="namespace">
    <name>siml</name>
    <filename>namespacesiml.html</filename>
    <class kind="struct">siml::parameter_descriptor</class>
    <class kind="struct">siml::variable_descriptor</class>
    <class kind="struct">siml::equation_descriptor</class>
    <class kind="struct">siml::model_descriptor</class>
    <class kind="struct">siml::model_grammar</class>
    <class kind="class">siml::name_grammar</class>
    <class kind="struct">siml::skip_grammar</class>
    <member kind="typedef">
      <type>std::vector&lt; parameter_descriptor &gt;</type>
      <name>parameter_table</name>
      <anchor>a0</anchor>
      <arglist></arglist>
    </member>
    <member kind="typedef">
      <type>std::vector&lt; variable_descriptor &gt;</type>
      <name>variable_table</name>
      <anchor>a1</anchor>
      <arglist></arglist>
    </member>
    <member kind="typedef">
      <type>std::vector&lt; equation_descriptor &gt;</type>
      <name>equation_table</name>
      <anchor>a2</anchor>
      <arglist></arglist>
    </member>
    <member kind="typedef">
      <type>std::vector&lt; model_descriptor &gt;</type>
      <name>model_table</name>
      <anchor>a3</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>siml::parameter_descriptor</name>
    <filename>structsiml_1_1parameter__descriptor.html</filename>
    <member kind="function">
      <type></type>
      <name>parameter_descriptor</name>
      <anchor>a0</anchor>
      <arglist>()</arglist>
    </member>
    <member kind="variable">
      <type>std::string</type>
      <name>name</name>
      <anchor>o0</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>std::string</type>
      <name>type</name>
      <anchor>o1</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>std::string</type>
      <name>default_expr</name>
      <anchor>o2</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>std::string</type>
      <name>definition_text</name>
      <anchor>o3</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>siml::variable_descriptor</name>
    <filename>structsiml_1_1variable__descriptor.html</filename>
    <member kind="function">
      <type></type>
      <name>variable_descriptor</name>
      <anchor>a0</anchor>
      <arglist>()</arglist>
    </member>
    <member kind="variable">
      <type>std::string</type>
      <name>name</name>
      <anchor>o0</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>std::string</type>
      <name>type</name>
      <anchor>o1</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>std::string</type>
      <name>definition_text</name>
      <anchor>o2</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>siml::equation_descriptor</name>
    <filename>structsiml_1_1equation__descriptor.html</filename>
    <member kind="function">
      <type></type>
      <name>equation_descriptor</name>
      <anchor>a0</anchor>
      <arglist>()</arglist>
    </member>
    <member kind="variable">
      <type>std::string</type>
      <name>lhs</name>
      <anchor>o0</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>std::string</type>
      <name>rhs</name>
      <anchor>o1</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>bool</type>
      <name>is_assignment</name>
      <anchor>o2</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>bool</type>
      <name>is_ode_assignment</name>
      <anchor>o3</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>std::string</type>
      <name>definition_text</name>
      <anchor>o4</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>siml::model_descriptor</name>
    <filename>structsiml_1_1model__descriptor.html</filename>
    <member kind="variable">
      <type>std::string</type>
      <name>name</name>
      <anchor>o0</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>parameter_table</type>
      <name>parameter</name>
      <anchor>o1</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>variable_table</type>
      <name>variable</name>
      <anchor>o2</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable">
      <type>equation_table</type>
      <name>equation</name>
      <anchor>o3</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>siml::model_grammar</name>
    <filename>structsiml_1_1model__grammar.html</filename>
    <base>boost::spirit::grammar</base>
    <class kind="struct">siml::model_grammar::definition</class>
  </compound>
  <compound kind="struct">
    <name>siml::model_grammar::definition</name>
    <filename>structsiml_1_1model__grammar_1_1definition.html</filename>
    <templarg>ScannerT</templarg>
    <member kind="function">
      <type></type>
      <name>definition</name>
      <anchor>a0</anchor>
      <arglist>(model_grammar const &amp;self)</arglist>
    </member>
    <member kind="function">
      <type>spirit::rule&lt; ScannerT &gt; const &amp;</type>
      <name>start</name>
      <anchor>a1</anchor>
      <arglist>() const </arglist>
    </member>
    <member kind="variable" protection="private">
      <type>spirit::rule&lt; ScannerT &gt;</type>
      <name>model_definition</name>
      <anchor>r0</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" protection="private">
      <type>spirit::rule&lt; ScannerT &gt;</type>
      <name>parameter_section</name>
      <anchor>r1</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" protection="private">
      <type>spirit::rule&lt; ScannerT &gt;</type>
      <name>parameter_definition</name>
      <anchor>r2</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" protection="private">
      <type>spirit::rule&lt; ScannerT &gt;</type>
      <name>variable_section</name>
      <anchor>r3</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" protection="private">
      <type>spirit::rule&lt; ScannerT &gt;</type>
      <name>variable_definition</name>
      <anchor>r4</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" protection="private">
      <type>spirit::rule&lt; ScannerT &gt;</type>
      <name>set_section</name>
      <anchor>r5</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" protection="private">
      <type>spirit::rule&lt; ScannerT &gt;</type>
      <name>parameter_assignment</name>
      <anchor>r6</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" protection="private">
      <type>spirit::rule&lt; ScannerT &gt;</type>
      <name>equation_section</name>
      <anchor>r7</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" protection="private">
      <type>spirit::rule&lt; ScannerT &gt;</type>
      <name>variable_assignment</name>
      <anchor>r8</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" protection="private">
      <type>spirit::rule&lt; ScannerT &gt;</type>
      <name>derivative_assignment</name>
      <anchor>r9</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" protection="private">
      <type>spirit::rule&lt; ScannerT &gt;</type>
      <name>rough_math_expression</name>
      <anchor>r10</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" protection="private">
      <type>name_grammar</type>
      <name>name</name>
      <anchor>r11</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" protection="private">
      <type>spirit::symbols</type>
      <name>param_name</name>
      <anchor>r12</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" protection="private">
      <type>spirit::symbols</type>
      <name>var_name</name>
      <anchor>r13</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="class">
    <name>siml::name_grammar</name>
    <filename>classsiml_1_1name__grammar.html</filename>
    <base>boost::spirit::grammar</base>
    <member kind="function">
      <type></type>
      <name>name_grammar</name>
      <anchor>a0</anchor>
      <arglist>(bool check_reserved_keywords=true)</arglist>
    </member>
    <member kind="variable">
      <type>spirit::symbols&lt; char &gt; const &amp;</type>
      <name>keywords</name>
      <anchor>o0</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" static="yes">
      <type>static spirit::symbols&lt; char &gt;</type>
      <name>reserved_keywords</name>
      <anchor>s0</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" protection="private">
      <type>spirit::symbols&lt; char &gt;</type>
      <name>dummy_reserved_keywords</name>
      <anchor>r0</anchor>
      <arglist></arglist>
    </member>
    <class kind="struct">siml::name_grammar::definition</class>
  </compound>
  <compound kind="struct">
    <name>siml::name_grammar::definition</name>
    <filename>structsiml_1_1name__grammar_1_1definition.html</filename>
    <templarg>ScannerT</templarg>
    <member kind="function">
      <type></type>
      <name>definition</name>
      <anchor>a0</anchor>
      <arglist>(name_grammar const &amp;self)</arglist>
    </member>
    <member kind="function">
      <type>spirit::rule&lt; ScannerT &gt; const &amp;</type>
      <name>start</name>
      <anchor>a1</anchor>
      <arglist>() const </arglist>
    </member>
    <member kind="variable" protection="private">
      <type>spirit::rule&lt; ScannerT &gt;</type>
      <name>name</name>
      <anchor>r0</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="struct">
    <name>siml::skip_grammar</name>
    <filename>structsiml_1_1skip__grammar.html</filename>
    <base>boost::spirit::grammar</base>
    <class kind="struct">siml::skip_grammar::definition</class>
  </compound>
  <compound kind="struct">
    <name>siml::skip_grammar::definition</name>
    <filename>structsiml_1_1skip__grammar_1_1definition.html</filename>
    <templarg>ScannerT</templarg>
    <member kind="function">
      <type></type>
      <name>definition</name>
      <anchor>a0</anchor>
      <arglist>(skip_grammar const &amp;)</arglist>
    </member>
    <member kind="function">
      <type>spirit::rule&lt; ScannerT &gt; const &amp;</type>
      <name>start</name>
      <anchor>a1</anchor>
      <arglist>() const </arglist>
    </member>
    <member kind="variable" protection="private">
      <type>spirit::rule&lt; ScannerT &gt;</type>
      <name>skip</name>
      <anchor>r0</anchor>
      <arglist></arglist>
    </member>
    <member kind="variable" protection="private">
      <type>spirit::rule&lt; ScannerT &gt;</type>
      <name>whitespace</name>
      <anchor>r1</anchor>
      <arglist></arglist>
    </member>
  </compound>
  <compound kind="namespace">
    <name>std</name>
    <filename>namespacestd.html</filename>
  </compound>
</tagfile>
