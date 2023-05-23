# `napkon_string_matching` Package

This package provides all functionality to match entries from Datensatztabellen from the NAPKON project. This allows to find common questions and build the basis to generate or update the GECCOplus FHIR profiles.

## `compare` Module

Functions to compare two entries with each other, see [compare/](compare)

## `prepare` Module

Prepares the dataset by generating tokens from the entry's phrases, see [prepare/](prepare)

## `terminology` Module

Providers to access data from different terminology systems to get all matching entries for a single term, see [terminology/](terminology)

## `test` Module

Unit test cases

## `types` Module

Holds all the different data classes ranging from `dataset_definition` to `mapping`, see [types/](types)
