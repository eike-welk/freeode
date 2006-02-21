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


#include "siml_ps_name.h"


namespace siml
{
    //Initialize the static symbol tables
    ps_name::symbol_table_t ps_name::reserved_keywords = init_reserved_keywords();
    ps_name::symbol_table_t ps_name::empty_table;

    /*!
    Initialize the symbol table "reserved_keywords" with the language's keywords.
    @todo split the symbol table up into section_headers = "PARAMETER", "UNIT" ... for better error recovery. After an error text could be skiped until the next ";" or the next section_headers.
    */
    ps_name::symbol_table_t ps_name::init_reserved_keywords()
    {
        symbol_table_t keywords;
        keywords =
            "MODEL","PARAMETER","DISTRIBUTION_DOMAIN","UNIT","VARIABLE",
            "SELECTOR","SET","BOUNDARY","EQUATION",
            "AS","ARRAY","OF","DEFAULT","DISTRIBUTION","STREAM","CONNECTION",
            "PROCESS","MONITOR","ASSIGN","PRESET","RESTORE","INITIAL",
            "STEADY_STATE","SOLUTIONPARAMETERS","SCHEDULE",
            "INTEGER","REAL","LOGICAL",
            "IF","ELSE","INTEGRAL",
    //         "TYPICAL",
            "time", "TIME", //special variable
            "END";
        return keywords;
    }
} // namespace siml
