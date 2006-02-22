/***************************************************************************
 *   Copyright (C) 2005 by Eike Welk   *
 *   eike.welk@post.rwth-aachen.de   *
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 *   This program is distributed in the hope that it will be useful,       *
 *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
 *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
 *   GNU General Public License for more details.                          *
 *                                                                         *
 *   You should have received a copy of the GNU General Public License     *
 *   along with this program; if not, write to the                         *
 *   Free Software Foundation, Inc.,                                       *
 *   59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.             *
 ***************************************************************************/
#include "siml_cmerror.h"

#include <iostream>
#include <boost/format.hpp>


using std::string;
using std::cerr;
using boost::format;


//static member initializer
siml::CmError::ErrorContainer siml::CmError::s_ErrorStorage;


siml::CmError::CmError(): m_severity(Error)
{
}


siml::CmError::~CmError()
{
}


/*!Add error to central storage.*/
void siml::CmError::addToStorage()
{
    s_ErrorStorage.push_back( *this);
}


/*!Add error to central storage.*/
// void siml::CmError::addToStorage(CmError const & error)
// {
//     s_ErrorStorage.push_back( error);
// }


/*!
Create a formated error message; create an error and put the message ito it.
Return the error without adding it to the central storage.

The function can cope with missing arguments, only message must always be given.

Currently the format is somewhat inspired by gcc's error messages:
/home/eike/.../src/siml_cmerror.cpp:66: error: syntax error before `}' token
 */
siml::CmError siml::CmError::createErrorFileLine(
        std::string const & message, std::string const & file, uint line, Severity howBad)
{
    string fileLineStr;
    if      ( line == 0 )    { fileLineStr = ""; }
    else if ( file.empty() ) { fileLineStr = (format("-no filename-:%1%: ") % line).str(); }
    else                     { fileLineStr = (format("%1%:%2%: ") % file % line).str(); }

    string howBadStr;
    if     ( howBad == Error )  { howBadStr = "error: "; }
    else if( howBad == Warnig ) { howBadStr = "warnig: "; }
    else                        { howBadStr = "info: "; }

    CmError theError;
    theError.m_severity = howBad;
    theError.m_message = fileLineStr + howBadStr + "\n" + message;

    return theError;
}


/*!
Alternative imlementation for error message generation. This works only with char const *.

Add some pieces of the program to the error message. This should show where the
error happened.
So the error can be located and understood more easylie.

@note protect against moving the iterator before the beginning or past the end of the buffer: append some \\n at begining and end
*/
siml::CmError siml::CmError::createErrorChar(std::string const & message, char const * where, Severity howBad)
{
    uint i, newlines;
    char const * offending_code_first = where;
    char const * offending_code_last  = where;
    std::string offending_code;

    if( where ) //protect aginst 0 pointer
    {
        //go one line up (move max 200 chars)
        for( i=0, newlines=0; i<200 && newlines<2; ++i, --offending_code_first )
        {
            if( *offending_code_first == '\n' ) { ++newlines; }
        }
        ++ ++offending_code_first;

        //go to next newline (move max 200 chars)
        for( i=0, offending_code_last; i<200 && *offending_code_last != '\n'; ++i, ++offending_code_last ) {}

        //put the two lines of program into a string
        offending_code = std::string( offending_code_first, offending_code_last);
    }

    string howBadStr;
    if     ( howBad == Error )  { howBadStr = "\nerror:\n"; }
    else if( howBad == Warnig ) { howBadStr = "\nwarnig:\n"; }
    else                        { howBadStr = "\ninfo:\n"; }

    //create error with nice message
    CmError theError;
    theError.m_severity = howBad;
    theError.m_message = offending_code + howBadStr + message;

    return theError;
}


/*!Dump the whole storage into cerr.*/
void siml::CmError::printStorage()
{
    ErrorContainer::const_iterator itE;
    for( itE = s_ErrorStorage.begin(); itE != s_ErrorStorage.end(); ++itE )
    {
        cerr << itE->m_message << "\n\n";
    }
}


