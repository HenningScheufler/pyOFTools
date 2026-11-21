/*---------------------------------------------------------------------------*\
            Copyright (c) 2026, Henning Scheufler
-------------------------------------------------------------------------------
License
    This file is part of the pyOFTools source code library, which is an
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

#ifndef Foam_pyOFTools_fpeGuard_H
#define Foam_pyOFTools_fpeGuard_H

#include "sigFpe.H"

#ifdef __linux__
    #include <fenv.h>
#endif

namespace Foam
{

// Disables OpenFOAM's FPE trap while Python runs, because numpy triggers
// floating point exceptions that are harmless to Python. On scope exit, also
// when Python raises, the trap is restored only if it was armed on entry: a
// solver keeps trapping, a Python host that disabled traps keeps them off, and
// a nested guard leaves re-arming to the outer one.
class FpeGuard
{
    const bool armed_;

    static bool trapsArmed()
    {
        #ifdef __linux__
        return
            sigFpe::active()
         && (fegetexcept() & (FE_DIVBYZERO | FE_INVALID | FE_OVERFLOW)) != 0;
        #else
        return sigFpe::active();
        #endif
    }

public:

    FpeGuard()
    :
        armed_(trapsArmed())
    {
        if (armed_)
        {
            sigFpe::unset(false);
        }
    }

    ~FpeGuard()
    {
        if (armed_)
        {
            sigFpe::set(false);
        }
    }

    FpeGuard(const FpeGuard&) = delete;
    FpeGuard& operator=(const FpeGuard&) = delete;
};

} // End namespace Foam

#endif

// ************************************************************************* //
