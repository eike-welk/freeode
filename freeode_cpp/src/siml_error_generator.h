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

#include "siml_code_model.h"

#include <string>


namespace siml {

/**
functor class to generate an error

	@author Eike Welk <eike.welk@post.rwth-aachen.de>
*/
class error_generator{
public:
    error_generator(std::string error_message, CmCodeRepository* repository);

    ~error_generator();

    //!Create the error.
    template <typename IteratorT>
    error_generator const&
    operator()(IteratorT first, IteratorT const& last) const
    {
        add_error(std::string(), std::string(), 0);
        return *this;
    }

    //!Add error to repository
    void add_error(std::string offending_code, std::string file, uint line) const;

    protected:
    //!The eror message
    std::string m_error_message;

    //!The code repository where the error will be put.
    CmCodeRepository* m_repository;
};

}

#endif
