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

Class
    Foam::pythonMixedFvPatchScalarField

Description
    Mixed boundary condition whose coefficients are computed by a Python
    class derived from pyOFTools.bc.MixedBC.

Usage
    \verbatim
    opening
    {
        type        pythonMixed;
        file        "system/boundary.py";   // relative to the case directory
        class       HotInflow;
        Tmean       300;                    // passed to the Python class
        value       uniform 300;
    }
    \endverbatim

    Python is started on the first updateCoeffs(), so utilities that only
    read or map the field (e.g. decomposePar) do not need an interpreter.

\*---------------------------------------------------------------------------*/

#ifndef pythonMixedFvPatchScalarField_H
#define pythonMixedFvPatchScalarField_H

#include <nanobind/nanobind.h>
#include "mixedFvPatchFields.H"

// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

namespace Foam
{

class pythonMixedFvPatchScalarField
:
    public mixedFvPatchScalarField
{
    // Private Data

        //- Python file, absolute or relative to the case directory
        fileName file_;

        //- Name of the Python class
        word className_;

        //- Entries forwarded to the Python class
        dictionary coeffs_;

        //- Python boundary condition, created on first update
        nanobind::object bc_;


    // Private Member Functions

        //- Start Python and create the boundary condition if needed
        void createPythonBC();

        //- Evaluate Python and store the mixed coefficients
        void updatePythonCoeffs();


public:

    //- Runtime type information
    TypeName("pythonMixed");


    // Constructors

        //- Construct from patch and internal field
        pythonMixedFvPatchScalarField
        (
            const fvPatch&,
            const DimensionedField<scalar, volMesh>&
        );

        //- Construct from patch, internal field and dictionary
        pythonMixedFvPatchScalarField
        (
            const fvPatch&,
            const DimensionedField<scalar, volMesh>&,
            const dictionary&
        );

        //- Construct by mapping onto a new patch
        pythonMixedFvPatchScalarField
        (
            const pythonMixedFvPatchScalarField&,
            const fvPatch&,
            const DimensionedField<scalar, volMesh>&,
            const fvPatchFieldMapper&
        );

        //- Copy construct
        pythonMixedFvPatchScalarField(const pythonMixedFvPatchScalarField&);

        //- Copy construct setting internal field reference
        pythonMixedFvPatchScalarField
        (
            const pythonMixedFvPatchScalarField&,
            const DimensionedField<scalar, volMesh>&
        );

        //- Return a clone
        virtual tmp<fvPatchScalarField> clone() const
        {
            return tmp<fvPatchScalarField>
            (
                new pythonMixedFvPatchScalarField(*this)
            );
        }

        //- Return a clone setting internal field reference
        virtual tmp<fvPatchScalarField> clone
        (
            const DimensionedField<scalar, volMesh>& iF
        ) const
        {
            return tmp<fvPatchScalarField>
            (
                new pythonMixedFvPatchScalarField(*this, iF)
            );
        }


    //- Destructor
    virtual ~pythonMixedFvPatchScalarField();


    // Member Functions

        //- Update the coefficients from Python
        virtual void updateCoeffs();

        //- Write
        virtual void write(Ostream&) const;
};


// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

} // End namespace Foam

// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

#endif

// ************************************************************************* //
