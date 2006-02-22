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
#ifndef SIMLSIML_CMERROR_H
#define SIMLSIML_CMERROR_H


#include <string>
// #include <vector>
#include <list>// #include <boost/shared_ptr.hpp>
#include <boost/spirit/iterator/position_iterator.hpp>


namespace siml {

/**
@short error message
An error message class with a central (static) storage.

	@author Eike Welk <eike.welk@post.rwth-aachen.de>
*/
class CmError{
public:
    //!Information how bad the error is.
    enum Severity { Error, Warnig, Info };
    //!Container for errors
    typedef std::list<CmError> ErrorContainer;

    /*!Constructor*/
    CmError();
    /*!Destructor*/
   ~CmError();

    /*!@return the error message*/
    std::string const & message() const { return m_message; }
    /*!@return the severity*/
    Severity severity() const { return m_severity; }

    //!Dump the whole storage into cerr.
    static void printStorage();

    //!Add error to central storage.
    void addToStorage();

    //!create error, put it into central storage
    /*!
    When you don't happen to have an iterator pass in 0 for where.
    The function simply calls createError(...) and the adds the error to the
    static storage.
    */
    template <typename IteratorT>
    static void addError(std::string const & message, IteratorT where, Severity howBad = Error)
    {
        CmError theError = createError( message, where, howBad);
        theError.addToStorage();
    }

    //!create error, return it
    /*!
    This is an unspecialized template function that just ignores the iterator
    and generates a simple error message.
    There are specilizations for IteratorT = const char *; and IteratorT = file line iterator;

    Template specilizations must be defined outside of the class. Reference:
    http://www.lrde.epita.fr/cgi-bin/twiki/view/Know/MemberFunctionsTemplateSpecialization
    */
    template <typename IteratorT>
    static CmError createError(std::string const & message, IteratorT /*where*/, Severity howBad)
    {
        ///@todo introduce the file line iterator
        std::string file;
        uint line = 0;
        return createErrorFileLine( message, file, line, howBad);
    }

    private:
    //!create error, return it.
    static CmError createErrorFileLine(std::string const & message, std::string const & file, uint line=0, Severity howBad = Error);
    //!create error, return it.
    static CmError createErrorChar(std::string const & message, char const * where, Severity howBad);

    //!Error message
    std::string m_message;
    //!Error type
    Severity m_severity;

    //!Central storage for all errors
    static ErrorContainer s_ErrorStorage;
};


//!create error, return it
/*!
Template specialization for char const *. Includes some of the errornous code into the error message.
Calls createErrorChar(...) to do the real work.

This is a fallback implementation when the position_iterator is unavaillable.
*/
template <>
inline CmError
CmError::createError< char const *>( std::string const & message, char const * where, Severity howBad)
{
    return createErrorChar( message, where, howBad);
}

//!create error, return it
/*!
Template specialization for file line iterator. This function asks the iterator
for the file and the line where the eror happened, and includes this information
in the error message.
Calls createErrorFileLine(...) to do the real work.
*/
template <>
inline CmError
CmError::createError< boost::spirit::position_iterator<char const *> > (
        std::string const & message,
        boost::spirit::position_iterator<char const *> where,
        Severity howBad)
{
    std::string file = where.get_position().file;
    uint line =  where.get_position().line;
    return createErrorFileLine( message, file, line, howBad);
}




}

#endif
