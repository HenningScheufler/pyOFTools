/*---------------------------------------------------------------------------*\
            Copyright (c) 2022, Henning Scheufler
-------------------------------------------------------------------------------
License
    This file is part of the pybFoam source code library, which is an
	unofficial extension to OpenFOAM.
    OpenFOAM is free software: you can redistribute it and/or modify it
    under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.
    OpenFOAM is distributed in the hope that it will be useful, but WITHOUT
    ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
    FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
    for more details.
    You should have received a copy of the GNU General Public License
    along with OpenFOAM.  If not, see <http://www.gnu.org/licenses/>.

\*---------------------------------------------------------------------------*/

#include "pyPostProcessing.hpp"
#include "Time.H"
#include "fvMesh.H"
#include "addToRunTimeSelectionTable.H"
#include "sigFpe.H"

// * * * * * * * * * * * * * * Static Data Members * * * * * * * * * * * * * //

namespace Foam
{
namespace functionObjects
{
    defineTypeNameAndDebug(pyPostProcessing, 0);
    addToRunTimeSelectionTable(functionObject, pyPostProcessing, dictionary);
}
}


// * * * * * * * * * * * * * * * * Constructors  * * * * * * * * * * * * * * //

Foam::functionObjects::pyPostProcessing::pyPostProcessing
(
    const word& name,
    const Time& runTime,
    const dictionary& dict
)
:
    fvMeshFunctionObject(name, runTime, dict),
    funcObj_
    (
        mesh_,
        dict.get<word>("pyFileName").c_str(),
        dict.get<word>("pyClassName").c_str()
    )
{
    read(dict);
}


// * * * * * * * * * * * * * * * Member Functions  * * * * * * * * * * * * * //

bool Foam::functionObjects::pyPostProcessing::read(const dictionary& dict)
{

    return true;
}


bool Foam::functionObjects::pyPostProcessing::execute()
{
    sigFpe::unset(false);
    bool success = funcObj_.execute();
    sigFpe::set(false);
    return success;
}


bool Foam::functionObjects::pyPostProcessing::end()
{
    sigFpe::unset(false);
    bool success = funcObj_.end();
    sigFpe::set(false);
    return success;
}


bool Foam::functionObjects::pyPostProcessing::write()
{
    sigFpe::unset(false);
    bool success = funcObj_.write();
    sigFpe::set(false);
    return success;
}


// ************************************************************************* //
