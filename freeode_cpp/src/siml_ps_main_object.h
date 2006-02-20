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
#ifndef PARSER_H
#define PARSER_H

#include "siml_code_model.h"
#include <boost/shared_ptr.hpp>


namespace siml
{

/**
@short The parser's main object
The class takes a pair of iterators into the input buffer, and generates a
representation in the static code repository of it (think of syntax tree).
The code repository is accessible throught a call to siml::repository()

The class' only purpose is to decouple the parser, that has very long compile
time, from the rest.

@author Eike Welk <eike.welk@post.rwth-aachen.de>
@version 0.1
*/
class ps_main_object
{
public:
    ps_main_object();

    ~ps_main_object();

    void doParse( BufferIterator bufBegin, BufferIterator bufEnd);
};

}
#endif
