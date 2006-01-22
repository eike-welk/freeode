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
#ifndef SIML_CMPATH_H
#define SIML_CMPATH_H


#include <string>
#include <list>


namespace siml {

/**
Long variable or paramer name with dots.

    @author Eike Welk <eike.welk@post.rwth-aachen.de>
*/
class CmPath{
public:
    CmPath();

    ~CmPath();

    //!Add string at begining
    void prepend(std::string const & compo);
    //!Add path at begining
    void prepend(CmPath const & inPath);
    //!Add string at end
    void append(std::string const & compo);
    //!Add path at end
    void append(CmPath const & inPath);

    //!Convert to string
    std::string toString(std::string const separatorStr = ".") const;

private:
    ///maybe use deque instead?
    typedef std::list<std::string> StringList;
    //!List of components
    StringList m_Component;
};

}

#endif // SIML_CMPATH_H
