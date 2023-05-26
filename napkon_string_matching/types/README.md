# `napkon_string_matching.types` Module

Here are all data classes defined that allow modification and file input and output. There are classes used in all different parts of the process and specializations (located in the `*_types` folders) that mostly focus on in- and output for different data sources.

`DatasetTable`, `KdsDefinition` and `GeccoDefinition` are responsible to handle and provide data that would be used for comparison and `Comparable` and `ComparableData` are involved in the the comparison itself.

## `base` Module

Base classes providing file input and output, see [base/](base).

## `dataset_table` Module

The information of _Datensatztabellen_ are handled by `DatasetTable` and its derived classes, see [dataset_table/](dataset_table).

## `gecco_definition_types` Module

Specializations of `GeccoDefinition` that provide input for GECCO83 and GECCOplus, see [gecco_definition_types/](gecco_definition_types).

## `kds_definition_types` Module

Different specializations to read KDS definitions, see [kds_definition_types/](kds_definition_types).

## `mapping_types` Module

Different specializations to handle mappings from various sources, see [mapping_types/](mapping_types).
