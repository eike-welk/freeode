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
#include "siml_globaldef.h"

#include "siml_code_model.h"
#include "siml_ps_main_object.h"
#include "siml_pygenmain.h"
#include "siml_cmerror.h"

// #include <boost/program_options.hpp>

#include <iostream>
#include <string>
#include <vector>
#include <algorithm>
#include <iterator>
// #include <streambuf>
#include <fstream>


using siml::ps_main_object;
using siml::PyGenMain;
using siml::CmError;
using siml::CmCodeRepository;

using std::cout;
using std::cerr;
using std::string;
using std::vector;
using std::ifstream;
using std::ofstream;
using std::istreambuf_iterator;
using std::copy;
using std::back_insert_iterator;


int main(int argc, char* argv[])
{
    string outputFile;
    vector< string> inputFileNames;
    uint debugLevel = 0;
//     uint messageLevel = 0;

    //parse the input by hand. (Boost command line argument lib makes problems.) -------------------------
    int iOpt;
    for( iOpt = 1; iOpt < argc; ++iOpt )
    {
        string currOpt = argv[iOpt];

        //show help text and return -------------------------------------------
        if( currOpt == "--help" )
        {
            cout << "Siml is a compiler and a programing language for differential equations.\n"
                    "Usage:\n"
                    "siml [options] <input files> ...\n"
                    "\n"
                    "Options:\n"
                    "--help Show this help text.\n"
                    "-v     Show program version.\n"
                    "-d     Show debug information. Use '-dd' or '-d -d' to increase output.\n"
//                     "-m     Show more messages. Use '-mm' or '-m -m' for more messages.\n"
                    "-o     Specify output file. If no output file is given the name of the\n"
                    "       first input file is used (with *.py extension).\n"
                    "\n"
                    "Everything with no leading '-' character is considered an input file.\n"
                    "\n"
                    ;
            return 0;
        }
        //show version --------------------------------------------------------
        else if( currOpt == "-v" )
        {
            cout << "siml version: " << VERSION << '\n';
        }
        //show debug output - -d  ... -ddddd  (okay it also takes: "-dqwert" etc.)
        else if( currOpt[0] == '-' && currOpt[1] == 'd' )
        {
            cerr << "siml: Debug output is currently unsupported.\n";
            debugLevel += currOpt.size()-1;
//             cout << "You want debug level: " << debugLevel << ".\n";
        }
//         else if( currOpt[0] == '-' && currOpt[1] == 'm' )
//         {
//             cout << "Message output is currently unsupported.\n";
//             messageLevel += currOpt.size()-1;
// //             cout << "You want debug level: " << debugLevel << ".\n";
//         }
        //output file specification----------------------------------------------
        else if( currOpt == "-o" )
        {
            if( ++iOpt >= argc )
            {
                cerr << "siml - Error: Name of output file required after '-o' option.\n";
                return 1;
            }
            outputFile = argv[iOpt];
        }
        //input file ----------------------------------------------------------
        else if( currOpt[0] != '-' )
        {
            inputFileNames.push_back( currOpt);
        }
        //error
        else
        {
            cerr << "siml - Error: Unknown option: " << argv[iOpt] << '\n';
            return 1;
        }
    }

    //complain if no input file is present.----------------------------------------------------------
    if( inputFileNames.size() == 0 )
    {
        cerr << "siml - Error: No input file(s).\n";
        return 1;
    }

    //Name the output file like the input file if no uotput file is specified. ----------------------
    //Conversion: name.* --> name.py
    if( outputFile.empty() )
    {
        outputFile = inputFileNames.front();
        //chop off everything behind the last dot (the extension).
        int posLastDot = outputFile.rfind( ".");
        if( posLastDot > 0 )
        {   //if there is a dot then chop. really if its at 2nd position or later
            int posEnd = outputFile.size()-1;
            outputFile.erase(posLastDot, posEnd);
        }
        //append Python extension to rest
        outputFile += ".py";
    }

    ///@todo this is debug output. (-m)
    //show what we're going to do -----------------------------------------------------------------------
//     vector< string>::iterator itS;
//     cout << "Input file(s):\n";
//     for( itS = inputFileNames.begin(); itS != inputFileNames.end(); ++itS){ cout << *itS << ", "; }
//     cout << '\n';
//     cout << "Output file:\n";
//     cout << outputFile << '\n';

    //put the file names into the code repository
    back_insert_iterator< vector<string> > insertStrings( CmCodeRepository::inputFileNames);
    copy(inputFileNames.begin(), inputFileNames.end(), insertStrings);

    //load the input files into memory and parse them -------------------------------------
    ///@todo a solution with #include style directives where much better.
    vector< string> inputBuffer;
    vector< string>::iterator itName;
    for( itName = inputFileNames.begin(); itName != inputFileNames.end(); ++itName)
    {
        //try to open the file
        ifstream inputStream( itName->c_str());
        if( !inputStream.is_open() )
        {   //The file does not exist. Abort the program.
            cerr << "siml - Error: Can not open input file: " << *itName << '\n';
            return 1;
        }

        //put new buffer into the list
        inputBuffer.push_back(string());
        //read the file's contents into the buffer
        istreambuf_iterator< char> itBegin( inputStream);
        istreambuf_iterator< char> itEnd;
        inputBuffer.back().append( itBegin, itEnd);
        //close the file
        inputStream.close();

        //create the iterators for the parser.
        BufferIterator begin(   inputBuffer.back().c_str(),
                                inputBuffer.back().c_str()+inputBuffer.back().size(),
                                *itName);
        BufferIterator end;
        //call the parser - results are stored in CmCodeRepository::repository
        ps_main_object parser;
        parser.doParse( begin, end);
    }

    ///@todo a separate call to generate the intermediate representation were good desingn.

    //code generation -----------------------------------------------------------------------------
    //open the output file.
    ofstream outputStream( outputFile.c_str()); //try to open the file
    if( !outputStream.is_open() )
    {   //The file does not exist. Abort program.
        cerr << "siml - Error: Can not open output file: " << outputFile << '\n';
        return 1;
    }
    //call the code generator - generate python program from CmCodeRepository::repository
    PyGenMain pyGen( outputStream);
    pyGen.generateAll();
    //close output file
    outputStream.close();
    //flush also the console buffer
    cout << std::endl;

    //print the errors
    CmError::printStorage();

    return 0;
}

