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

#include "siml_code_model.h"

#include <iostream>

using std::cout;
using std::endl;

/*!Iterate through all lists and display their contents.*/
void
siml::CmModelDescriptor::display() const
{
    cout << "model: " << name << endl;
    cout << "parameters:" << endl;
    for(uint i=0; i<parameter.size(); ++i) {
        cout << "|  " << parameter[i].name << ", " << parameter[i].type << ", " << parameter[i].default_expr << endl;
    }

    cout << "sub models:" << endl;
    for(uint i=0; i<subModel.size(); ++i) {
        cout << "|  " << subModel[i].name << endl;
    }

    cout << "variables:" << endl;
    for(uint i=0; i<variable.size(); ++i) {
        cout << "|  " << variable[i].name << ", " << variable[i].type << endl;
    }

    cout << "equations:" << endl;
//     uint es=equation.size();
    for(uint i=0; i<equation.size(); ++i) {
//         cout << equation[i].definition_text << endl;
        cout << "|  "  << equation[i].lhs;
        cout << "  :=  " << equation[i].rhs;
        if( equation[i].is_ode_assignment ) {
            cout << "  - ODE" << endl;
        } else {
            cout << "  - algebraic" << endl;
        }
    }
}


/*!Iterate through all lists and display their contents.*/
void
siml::CmProcessDescriptor::display() const
{
    cout << "process ";
    CmModelDescriptor::display();

/*    cout << "initial expressions:" << endl;
    uint es=equation.size();
    for(uint i=0; i<initialExpression.size(); ++i) {
        cout << equation[i].definition_text << endl;
        cout << "|  "  << equation[i].lhs;
        cout << "  :=  " << equation[i].rhs;
    }*/
}


/*!Iterate through all lists and display their contents.*/
void
siml::CmCodeRepository::display() const
{
    cout << "models ----------------------------------" << endl;
    for( uint i=0; i < model.size(); ++i )
    {
        model[i].display();
        cout<<endl;
    }

    cout << "processes ----------------------------------" << endl;
    for( uint i=0; i < process.size(); ++i )
    {
        process[i].display();
        cout<<endl;
    }

    cout << "errors -----------------------------" << endl;
    for( uint i=0; i < error.size(); ++i )
    {
        cout << error[i].error_message << endl;
    }
    cout << "------------------------------------" << endl;
}
