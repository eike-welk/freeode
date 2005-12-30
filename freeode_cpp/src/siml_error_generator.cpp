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
#include "siml_error_generator.h"

siml::error_generator::error_generator(std::string error_message, CmErrorDescriptor& error) :
        m_error_message(error_message),
//         m_repository(repository)
        m_error(error)
{
}


siml::error_generator::~error_generator()
{
}


/*!
Add an error to the repository
*/
void
siml::error_generator::add_error(char const * offending_code_first, char const * offending_code_last) const
{
    //offending_code_first, offending_code_last point usually to the same byte
    uint i, newlines;

    //go one line up
    for( i=0, newlines=0; i<200 && newlines<2; ++i, --offending_code_first )
    {
        if( *offending_code_first == '\n' ) { ++newlines; }
    }
    ++ ++offending_code_first;

    //go to next newline
    for( i=0, offending_code_last; i<200 && *offending_code_last != '\n'; ++i, ++offending_code_last ) {}

    //create error message
    std::string offending_code(offending_code_first, offending_code_last);
    CmErrorDescriptor the_error;
    the_error.error_message = offending_code + "\n" + m_error_message + "\n";

//     m_repository->error.push_back(the_error);
    m_error = the_error;
}
