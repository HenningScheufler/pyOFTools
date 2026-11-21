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

#include "pythonMixedFvPatchScalarField.hpp"

#include <nanobind/ndarray.h>
#include <nanobind/stl/string.h>

#include "addToRunTimeSelectionTable.H"
#include "fvPatchFieldMapper.H"
#include "nanobindEmbed.hpp"
#include "pyInterp.hpp"
#include "sigFpe.H"
#include "StringStream.H"
#include "surfaceFields.H"
#include "volFields.H"

namespace nb = nanobind;

// * * * * * * * * * * * * * * Local Functions * * * * * * * * * * * * * * * //

namespace
{

using namespace Foam;

using ReadOnlyArray = nb::ndarray<nb::numpy, const scalar, nb::c_contig>;
using InputArray = nb::ndarray<const double, nb::ndim<1>, nb::c_contig>;

// Empty OpenFOAM lists may have a null data pointer, which numpy rejects
const scalar emptyData = 0;

nb::object toNumpy(const scalarField& fld)
{
    const size_t shape[1] = {size_t(fld.size())};
    const scalar* data = fld.empty() ? &emptyData : fld.cdata();
    return nb::cast(ReadOnlyArray(data, 1, shape, nb::handle()));
}

nb::object toNumpy(const vectorField& fld)
{
    const size_t shape[2] = {size_t(fld.size()), 3};
    const scalar* data =
        fld.empty()
      ? &emptyData
      : reinterpret_cast<const scalar*>(fld.cdata());
    return nb::cast(ReadOnlyArray(data, 2, shape, nb::handle()));
}

void assignField(scalarField& fld, nb::handle values)
{
    const InputArray input = nb::cast<InputArray>(values);

    if (input.size() != size_t(fld.size()))
    {
        FatalErrorInFunction
            << "Python returned " << label(input.size())
            << " values for a patch with " << fld.size() << " faces"
            << exit(FatalError);
    }

    forAll(fld, facei)
    {
        fld[facei] = input(facei);
    }
}

// Restores OpenFOAM's FPE trap, also when Python raises an exception.
// numpy triggers floating point exceptions that are harmless to Python.
struct FpeGuard
{
    FpeGuard() { sigFpe::unset(false); }
    ~FpeGuard() { sigFpe::set(false); }
};

} // End anonymous namespace


// * * * * * * * * * * * * * Private Member Functions  * * * * * * * * * * * //

void Foam::pythonMixedFvPatchScalarField::createPythonBC()
{
    if (bc_.is_valid())
    {
        return;
    }

    const Time& runTime = db().time();
    pyInterp::New(runTime);

    // Sets this library's nanobind state, which every cast below relies on
    initEmbeddedNanobind();

    const fileName path =
        file_.isAbsolute() ? file_ : fileName(runTime.globalPath()/file_);

    nb::dict coeffs;
    for (const entry& e : coeffs_)
    {
        if (!e.isStream())
        {
            FatalIOErrorInFunction(coeffs_)
                << "Entry " << e.keyword()
                << " must be a value, not a sub-dictionary"
                << exit(FatalIOError);
        }

        OStringStream os;
        const ITstream& tokens = e.stream();
        for (label i = 0; i < tokens.size(); ++i)
        {
            if (i)
            {
                os << ' ';
            }
            os << tokens[i];
        }
        coeffs[e.keyword().c_str()] = static_cast<const std::string&>(os.str());
    }

    bc_ = nb::module_::import_("pyOFTools.bc").attr("_create")
    (
        std::string(path),
        std::string(className_),
        coeffs,
        std::string(patch().name()),
        std::string(internalField().name())
    );
}


void Foam::pythonMixedFvPatchScalarField::updatePythonCoeffs()
{
    createPythonBC();

    const fvPatch& p = patch();

    nb::object phi = nb::none();
    if (db().foundObject<surfaceScalarField>("phi"))
    {
        phi = toNumpy
        (
            static_cast<const scalarField&>
            (
                p.lookupPatchField<surfaceScalarField>("phi")
            )
        );
    }

    const nb::tuple result = nb::cast<nb::tuple>
    (
        nb::module_::import_("pyOFTools.bc").attr("_evaluate")
        (
            bc_,
            db().time().value(),
            toNumpy(p.Cf()),
            toNumpy(p.Sf()),
            toNumpy(p.magSf()),
            phi
        )
    );

    assignField(refValue(), result[0]);
    assignField(refGrad(), result[1]);
    assignField(valueFraction(), result[2]);
}


// * * * * * * * * * * * * * * * * Constructors  * * * * * * * * * * * * * * //

Foam::pythonMixedFvPatchScalarField::pythonMixedFvPatchScalarField
(
    const fvPatch& p,
    const DimensionedField<scalar, volMesh>& iF
)
:
    mixedFvPatchScalarField(p, iF),
    file_(),
    className_(),
    coeffs_(),
    bc_()
{
    refValue() = Zero;
    refGrad() = Zero;
    valueFraction() = 1;
}


Foam::pythonMixedFvPatchScalarField::pythonMixedFvPatchScalarField
(
    const fvPatch& p,
    const DimensionedField<scalar, volMesh>& iF,
    const dictionary& dict
)
:
    mixedFvPatchScalarField(p, iF),
    file_(dict.get<fileName>("file").expand()),
    className_(dict.get<word>("class")),
    coeffs_(dict),
    bc_()
{
    fvPatchFieldBase::readDict(dict);

    for
    (
        const word key
      : {"type", "patchType", "file", "class", "value",
         "refValue", "refGradient", "valueFraction", "source"}
    )
    {
        coeffs_.remove(key);
    }

    this->readValueEntry(dict, IOobjectOption::MUST_READ);

    refValue() = *this;
    refGrad() = Zero;
    valueFraction() = 1;
}


Foam::pythonMixedFvPatchScalarField::pythonMixedFvPatchScalarField
(
    const pythonMixedFvPatchScalarField& ptf,
    const fvPatch& p,
    const DimensionedField<scalar, volMesh>& iF,
    const fvPatchFieldMapper& mapper
)
:
    mixedFvPatchScalarField(ptf, p, iF, mapper),
    file_(ptf.file_),
    className_(ptf.className_),
    coeffs_(ptf.coeffs_),
    bc_()   // The patch changed, so Python is recreated on the next update
{}


Foam::pythonMixedFvPatchScalarField::pythonMixedFvPatchScalarField
(
    const pythonMixedFvPatchScalarField& ptf
)
:
    pythonMixedFvPatchScalarField(ptf, ptf.internalField())
{}


Foam::pythonMixedFvPatchScalarField::pythonMixedFvPatchScalarField
(
    const pythonMixedFvPatchScalarField& ptf,
    const DimensionedField<scalar, volMesh>& iF
)
:
    mixedFvPatchScalarField(ptf, iF),
    file_(ptf.file_),
    className_(ptf.className_),
    coeffs_(ptf.coeffs_),
    bc_(ptf.bc_)
{}


// * * * * * * * * * * * * * * * * Destructor  * * * * * * * * * * * * * * * //

Foam::pythonMixedFvPatchScalarField::~pythonMixedFvPatchScalarField()
{
    // The reference cannot be dropped once the interpreter has shut down
    if (bc_.is_valid() && !Py_IsInitialized())
    {
        bc_.release();
    }
}


// * * * * * * * * * * * * * * * Member Functions  * * * * * * * * * * * * * //

void Foam::pythonMixedFvPatchScalarField::updateCoeffs()
{
    if (updated())
    {
        return;
    }

    {
        FpeGuard guard;

        try
        {
            updatePythonCoeffs();
        }
        catch (const nb::python_error& err)
        {
            FatalErrorInFunction
                << "Python boundary condition " << className_
                << " from " << file_ << " failed on patch "
                << patch().name() << " of field "
                << internalField().name() << nl
                << err.what()
                << exit(FatalError);
        }
    }

    mixedFvPatchScalarField::updateCoeffs();
}


void Foam::pythonMixedFvPatchScalarField::write(Ostream& os) const
{
    fvPatchField<scalar>::write(os);
    os.writeEntry("file", file_);
    os.writeEntry("class", className_);
    coeffs_.writeEntries(os);
    fvPatchField<scalar>::writeValueEntry(os);
}


// * * * * * * * * * * * * * * Runtime Selection * * * * * * * * * * * * * * //

namespace Foam
{
    makePatchTypeField
    (
        fvPatchScalarField,
        pythonMixedFvPatchScalarField
    );
}

// ************************************************************************* //
