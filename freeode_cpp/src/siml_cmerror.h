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
#include <list>
// #include <boost/shared_ptr.hpp>


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

    CmError();

    ~CmError();

    /*!@return the error message*/
    std::string const & message() const { return m_message; }
    /*!@return the severity*/
    Severity severity() const { return m_severity; }

    //!Add error to central storage.
    void addToStorage();

    //!create error, put it into central storage
    /*!When you don't happen to have an iterator pass in 0 for where. */
    template <typename IteratorT>
    static void addError(std::string const & message, IteratorT where, Severity howBad = Error)
    {
        CmError theError = createError( message, where, howBad);
        theError.addToStorage();
    }

    //!create error, return it
    /*!This function asks the iterator for the file and the line where the eror happened.*/
    template <typename IteratorT>
    static CmError createError(std::string const & message, IteratorT /*where*/, Severity howBad)
    {
        ///@todo introduce the file line iterator
        std::string file;
        uint line = 0;
        return createError( message, file, line, howBad);
    }

    private:
    //!create error, return it.
    static CmError createError(std::string const & message, std::string const & file, uint line=0, Severity howBad = Error);
    //!create error, return it.
    static CmError createErrorChar(std::string const & message, char const * where, Severity howBad);
    public:

    //!Dump the whole storage into cerr.
    static void printStorageToCerr();

    //!Error message
    std::string m_message;
    //!Error type
    Severity m_severity;

    //!Central storage for all errors
    static ErrorContainer s_ErrorStorage;
};


//!create error, return it
/*!
Template specialization for char const *. Includes some of the errornous code into the error message. See:
http://www.lrde.epita.fr/cgi-bin/twiki/view/Know/MemberFunctionsTemplateSpecialization
 */
template <>
inline CmError CmError::createError<char const *>(std::string const & message, char const * where, Severity howBad)
{
    return createErrorChar( message, where, howBad);
}

}

#endif
