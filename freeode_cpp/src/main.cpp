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
    vector< string> inputFiles;
    uint debugLevel = 0;
    uint messageLevel = 0;

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
            cerr << "siml version: " << VERSION << '\n';
        }
        //show debug output - -d  ... -ddddd  (okay it also takes: "-dqwert" etc.)
        else if( currOpt[0] == '-' && currOpt[1] == 'd' )
        {
            cerr << "Debug output is currently unsupported.\n";
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
                cerr << "Error: Name of output file required after '-o' option.\n";
                return 1;
            }
            outputFile = argv[iOpt];
        }
        //input file ----------------------------------------------------------
        else if( currOpt[0] != '-' )
        {
            inputFiles.push_back( currOpt);
        }
        //error
        else
        {
            cerr << "Unknown option: " << argv[iOpt] << '\n';
            return 1;
        }
    }

    //complain if no input file is present.----------------------------------------------------------
    if( inputFiles.size() == 0 )
    {
        cerr << "Error: No input file(s).\n";
        return 1;
    }

    //create the output file name if none given (name.* --> name.py) -------------------------------------
    if( outputFile.empty() )
    {
        outputFile = inputFiles.front();
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
    vector< string>::iterator itS;
//     cout << "Input file(s):\n";
//     for( itS = inputFiles.begin(); itS != inputFiles.end(); ++itS){ cout << *itS << ", "; }
//     cout << '\n';
//     cout << "Output file:\n";
//     cout << outputFile << '\n';

    //put the file names into the code repository
    back_insert_iterator< vector<string> > insertStrings( CmCodeRepository::inputFileNames);
    copy(inputFiles.begin(), inputFiles.end(), insertStrings);

    ///@todo a solution with #include style directives where much better.
    //load the input files into memory and concatenate them-------------------------------------
    string pading = "\n\n\n"; //protect against iterating beyond begin or end by the error generation function.
    string inputStr = pading; //The buffer, all files go here.
//     vector< string>::iterator itS;
    for( itS = inputFiles.begin(); itS != inputFiles.end(); ++itS)
    {
        ifstream inputStream( itS->c_str()); //try to open the file
        if( !inputStream.is_open() )
        {   //The file does not exist.
            cerr << "Error: Can not open input file: " << *itS << '\n';
            return 1;
        }
        //append the file to the buffer
        istreambuf_iterator< char> itBegin( inputStream);
        istreambuf_iterator< char> itEnd;
        inputStr.append( itBegin, itEnd);
        inputStr.append( pading.begin(), pading.end()); //append some return chars after each file
        inputStream.close();
    }

    ///@todo this is debug output. (-mmm)
//     cout << "The input: \n";
//     cout << "-----------------------------------------------------\n";
//     cout << inputStr;
//     cout << "-----------------------------------------------------\n\n";

    //Parsing ----------------------------------------------------------------------------------
    //create the iterators for the parser.
    ///@todo using different iterators than "char const *" does not work.
//     typedef position_iterator<char const *> IteratorT;
//     IteratorT begin(inputCStr, inputCStr+strlen(inputCStr), "test.file");
//     IteratorT end;
    BufferIterator begin = inputStr.c_str();  //BufferIterator ~ char const *
    BufferIterator end = begin+inputStr.size(); //strlen(inputCStr);
    //call the parser - results are stored in CmCodeRepository::repository
    ps_main_object parser;
    parser.doParse( begin, end);

    ///@todo a separate call to generate the intermediate representation were good desingn.

    //code generation -----------------------------------------------------------------------------
    //open the output file.
    ofstream outputStream( outputFile.c_str()); //try to open the file
    if( !outputStream.is_open() )
    {   //The file does not exist.
        cerr << "Error: Can not open output file: " << outputFile << '\n';
        return 1;
    }
    //call the code generator - generate python program from CmCodeRepository::repository
    PyGenMain pyGen( outputStream);
    pyGen.generateAll();

    outputStream.close();

    //print the errors
    CmError::printStorageToCerr();

    return 0;
}

