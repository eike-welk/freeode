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
#include <iostream>


namespace siml {

/**
Long variable or paramer name with dots.

    @author Eike Welk <eike.welk@post.rwth-aachen.de>
*/
class CmPath{
public:
    //!create empty path
    CmPath();
    //!Initialize with one component
    CmPath(std::string const & contentsNew);
    //!Initialize with one component
    /*!No parsing is done.*/
    template <class InputIterator> CmPath(InputIterator first, InputIterator last)
    { set(std::string(first, last)); }

    ~CmPath();

    //!compare with string        @todo Marshal Cline says: the function should be private
    bool isEqual(std::string const & inString) const;
    //!compare with CmPath        @todo Marshal Cline says: the function should go away
    bool isEqual(CmPath const & inPath) const;
    //!compare with CmPath
    bool operator==(CmPath const & inPath) const { return isEqual(inPath); }

    //!remove all components
    CmPath & clear();
    //!Let path contain one single string
    CmPath & set(std::string const & contentsNew);
    //!Copy all components
    CmPath & set(CmPath const & contentsNew);
    //!Add string at begining
    CmPath & prepend(std::string const & compo);
    //!Add path at begining
    CmPath & prepend(CmPath const & inPath);
    //!Add string at end
    CmPath & append(std::string const & compo);
    //!Add path at end
    CmPath & append(CmPath const & inPath);

    //!Convert to string
    std::string toString(std::string const separatorStr = ".") const;

private:
    ///maybe use deque instead?
    typedef std::list<std::string> StringList;
    //!List of components
    StringList m_Component;
};

//!compare with string
inline bool operator==(std::string const & p1, CmPath const & p2) { return p2.isEqual(p1); }
//!compare with string
inline bool operator==(CmPath const & p1, std::string const & p2) { return p1.isEqual(p2); }

//!printing
std::ostream& operator<<(std::ostream& out, siml::CmPath const & path);

}

#endif // SIML_CMPATH_H
