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
#ifndef SIML_GLOBALDEF_H
#define SIML_GLOBALDEF_H

#include "config.h"
#include <boost/spirit/iterator.hpp>
// #include <boost/spirit/iterator/position_iterator.hpp>

//!Simple iterator for the program text
// typedef char const * BufferIterator;

//!Iterator that can be asked for the current file name and line.
/*!The underlying buffer is still a char array. Directly wraping
a stream iterator is impossible because spirit is a backtracking parser.*/
typedef boost::spirit::position_iterator<char const *> BufferIterator;

#endif


