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
#ifndef SIMLSIML_ERROR_GENERATOR_H
#define SIMLSIML_ERROR_GENERATOR_H


#include "siml_cmerror.h"

#include <string>


namespace siml {

/**
@short error generator
This functor class generates an error and adds it to the central error storage.
It can be used in semantic actions of the spirit parser framework. e.g.:
@code >> myrule[add_error("This is bad!", CmError::Warning)] >> @endcode
When the parse rule matches the spirit framework calles the operator()(T, T) function.
This function will generate and handle the error.

@author Eike Welk <eike.welk@post.rwth-aachen.de>
*/
struct add_error {
    //!temporary storage for the error message (until the functor is invoked).
    std::string m_message;
    //!temporary storage for the error's type
    CmError::Severity m_severity;

    //!Constructor: store information for error generation.
    add_error(  std::string error_message,
                CmError::Severity error_severity = CmError::Error ):
            m_message( error_message), m_severity( error_severity) {}

    //!Create the error, add it to the central storage.
    template <typename IteratorT>
    void operator()(IteratorT first, IteratorT) const
    {
        CmError::addError( m_message, first, m_severity);
    }
};


/**
@short error generator
This functor class generates an error and stores it in a user supplied location.
It can be used in semantic actions of the spirit parser framework. e.g.:
@code >> myrule[add_error(temp_error, "This is bad!", CmError::Warning)] >> @endcode
When the parse rule matches the spirit framework calles the operator()(T, T) function.
This function will generate and handle the error.

@author Eike Welk <eike.welk@post.rwth-aachen.de>
 */
struct create_error {
    //!object where generated error will be stored
    CmError & m_error;
    //!temporary storage for the error message (until the functor is invoked).
    std::string m_message;
    //!temporary storage for the error's type
    CmError::Severity m_severity;

    //!Constructor: store information for error generation.
    create_error(   CmError & error,
                    std::string error_message,
                    CmError::Severity error_severity = CmError::Error ):
            m_error( error), m_message( error_message), m_severity( error_severity) {}

    //!Create the error, store it.
    template <typename IteratorT>
    void operator()(IteratorT first, IteratorT) const
    {
        m_error = CmError::createError( m_message, first, m_severity);
    }
};
}

#endif
