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

siml::error_generator::error_generator(std::string error_message, CmCodeRepository* repository) :
        m_error_message(error_message),
        m_repository(repository)
{
}


siml::error_generator::~error_generator()
{
}


/*!
Add an error to the repository
*/
void siml::error_generator::add_error(std::string offending_code, std::string file, uint line) const
{
    CmErrorDescriptor the_error;
    the_error.error_message = m_error_message;

    m_repository->error.push_back(the_error);
}
