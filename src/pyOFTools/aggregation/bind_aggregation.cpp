/*---------------------------------------------------------------------------*\
            Copyright (c) 20212, Henning Scheufler
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

#include "bind_aggregation.hpp"

namespace nb = nanobind;

template <class Type>
struct aggregationResult
{
    Foam::Field<Type> values;
    std::optional<Foam::labelList> group = std::nullopt;
};

template <typename T>
aggregationResult<T> aggSum(
    const Foam::Field<T> &values,
    std::optional<Foam::boolList> mask = std::nullopt,
    std::optional<Foam::labelList> group = std::nullopt,
    std::optional<Foam::scalarField> scalingFactor = std::nullopt)
{
    aggregationResult<T> result;
    auto nGroups = group ? max(*group) + 1 : 1;
    result.values = Foam::Field<T>(nGroups, Foam::Zero);
    // store the group information in the result
    // ranging from 0 to nGroups-1
    // if no grouping is done, this remains nullopt
    if (group)
    {
        result.group = Foam::labelList(nGroups);
        for (Foam::label i = 0; i < nGroups; ++i)
        {
            (*result.group)[i] = i;
        }
    }

    const Foam::label nElements = values.size();

    for (Foam::label i = 0; i < nElements; ++i)
    {
        Foam::label groupIndex = group ? (*group)[i] : 0;
        Foam::scalar masking = mask ? (*mask)[i] : 1.0;
        Foam::scalar scaleFactor = scalingFactor ? (*scalingFactor)[i] : 1.0;
        result.values[groupIndex] += values[i] * masking * scaleFactor;
    }

    Foam::reduce(result.values, Foam::sumOp<Foam::Field<T>>());

    return result;
}


template <typename T>
aggregationResult<T> aggMean(
    const Foam::Field<T> &values,
    std::optional<Foam::boolList> mask = std::nullopt,
    std::optional<Foam::labelList> group = std::nullopt,
    std::optional<Foam::scalarField> scalingFactor = std::nullopt)
{
    aggregationResult<T> result;
    auto nGroups = group ? max(*group) + 1 : 1;
    result.values = Foam::Field<T>(nGroups, Foam::Zero);
    Foam::Field<Foam::scalar> weights(nGroups, 0.0);
    // store the group information in the result
    // ranging from 0 to nGroups-1
    // if no grouping is done, this remains nullopt
    if (group)
    {
        result.group = Foam::labelList(nGroups);
        for (Foam::label i = 0; i < nGroups; ++i)
        {
            (*result.group)[i] = i;
        }
    }

    const Foam::label nElements = values.size();

    for (Foam::label i = 0; i < nElements; ++i)
    {
        Foam::label groupIndex = group ? (*group)[i] : 0;
        Foam::scalar masking = mask ? (*mask)[i] : 1.0;
        Foam::scalar scaleFactor = scalingFactor ? (*scalingFactor)[i] : 1.0;
        result.values[groupIndex] += values[i] * masking * scaleFactor;
        weights[groupIndex] += masking * scaleFactor;
    }

    Foam::reduce(result.values, Foam::sumOp<Foam::Field<T>>());
    Foam::reduce(weights, Foam::sumOp<Foam::Field<Foam::scalar>>());

    for (Foam::label i = 0; i < nGroups; ++i)
    {
        if (weights[i] > Foam::SMALL)
        {
            result.values[i] /= weights[i];
        }
        else
        {
            if constexpr (std::is_same<T, Foam::scalar>::value)
            {
                result.values[i] = Foam::GREAT; // if no valid entries, set to large value
            }
            else
            {
                result.values[i] = T::one * Foam::GREAT;
            }
        }
    }

    return result;
}

template <typename T>
aggregationResult<T> aggMax(
    const Foam::Field<T> &values,
    std::optional<Foam::boolList> mask = std::nullopt,
    std::optional<Foam::labelList> group = std::nullopt)
{
    aggregationResult<T> result;
    auto nGroups = group ? max(*group) + 1 : 1;
    // store the group information in the result
    // ranging from 0 to nGroups-1
    // if no grouping is done, this remains nullopt
    if (group)
    {
        result.group = Foam::labelList(nGroups);
        for (Foam::label i = 0; i < nGroups; ++i)
        {
            (*result.group)[i] = i;
        }
    }
    if constexpr (std::is_same<T, Foam::scalar>::value)
    {
        result.values = Foam::Field<T>(nGroups, -Foam::GREAT);
    }
    else
    {
        result.values = Foam::Field<T>(nGroups, T::one * -Foam::GREAT);
    }

    const Foam::label nElements = values.size();

    for (Foam::label i = 0; i < nElements; ++i)
    {
        Foam::label groupIndex = group ? (*group)[i] : 0;
        if (mask)
        {
            if (!(*mask)[i]) // if mask is false, skip
            {
                continue;
            }
        }
        result.values[groupIndex] = Foam::max(result.values[groupIndex], values[i]);
    }

    Foam::reduce(result.values, Foam::maxOp<Foam::Field<T>>());

    return result;
}

template <typename T>
aggregationResult<T> aggMin(
    const Foam::Field<T> &values,
    std::optional<Foam::boolList> mask = std::nullopt,
    std::optional<Foam::labelList> group = std::nullopt)
{
    aggregationResult<T> result;
    auto nGroups = group ? max(*group) + 1 : 1;
    // store the group information in the result
    // ranging from 0 to nGroups-1
    // if no grouping is done, this remains nullopt
    if (group)
    {
        result.group = Foam::labelList(nGroups);
        for (Foam::label i = 0; i < nGroups; ++i)
        {
            (*result.group)[i] = i;
        }
    }

    if constexpr (std::is_same<T, Foam::scalar>::value)
    {
        result.values = Foam::Field<T>(nGroups, Foam::GREAT);
    }
    else
    {
        result.values = Foam::Field<T>(nGroups, T::one * Foam::GREAT);
    }

    const Foam::label nElements = values.size();

    for (Foam::label i = 0; i < nElements; ++i)
    {
        Foam::label groupIndex = group ? (*group)[i] : 0;
        if (mask)
        {
            if (!(*mask)[i]) // if mask is false, skip
            {
                continue;
            }
        }
        result.values[groupIndex] = Foam::min(result.values[groupIndex], values[i]);
    }

    Foam::reduce(result.values, Foam::minOp<Foam::Field<T>>());

    return result;
}

void Foam::bindAggregation(nb::module_ &m)
{

    nb::class_<aggregationResult<scalar>>(m, "scalarAggregationResult")
        .def_ro("values", &aggregationResult<scalar>::values)
        .def_ro("group", &aggregationResult<scalar>::group);

    nb::class_<aggregationResult<vector>>(m, "vectorAggregationResult")
        .def_ro("values", &aggregationResult<vector>::values)
        .def_ro("group", &aggregationResult<vector>::group);

    m.def("sum", &aggSum<scalar>, nb::arg("values"), nb::arg("mask") = std::nullopt, nb::arg("group") = std::nullopt, nb::kw_only(), nb::arg("scalingFactor") = std::nullopt);
    m.def("sum", &aggSum<vector>, nb::arg("values"), nb::arg("mask") = std::nullopt, nb::arg("group") = std::nullopt, nb::kw_only(), nb::arg("scalingFactor") = std::nullopt);

    m.def("mean", &aggMean<scalar>, nb::arg("values"), nb::arg("mask") = std::nullopt, nb::arg("group") = std::nullopt, nb::kw_only(), nb::arg("scalingFactor") = std::nullopt);
    m.def("mean", &aggMean<vector>, nb::arg("values"), nb::arg("mask") = std::nullopt, nb::arg("group") = std::nullopt, nb::kw_only(), nb::arg("scalingFactor") = std::nullopt);

    m.def("max", &aggMax<scalar>, nb::arg("values"), nb::arg("mask") = std::nullopt, nb::arg("group") = std::nullopt);
    m.def("max", &aggMax<vector>, nb::arg("values"), nb::arg("mask") = std::nullopt, nb::arg("group") = std::nullopt);

    m.def("min", &aggMin<scalar>, nb::arg("values"), nb::arg("mask") = std::nullopt, nb::arg("group") = std::nullopt);
    m.def("min", &aggMin<vector>, nb::arg("values"), nb::arg("mask") = std::nullopt, nb::arg("group") = std::nullopt);
}
