# `napkon_string_matching` Package

This package provides all functionality to match entries from Datensatztabellen from the NAPKON project. This allows to find common questions and build the basis to generate or update the GECCOplus FHIR profiles.

The process of the tool is coodintated in the `matching` module. It constructs the needed matching classes and performs the `variables`, `gecco` and `questionnaires` steps.

THe matching itself is done by `Matcher`. It loads all data for Datensatztabellen, GECCO definitions, existing mappings and others from disk and triggers the comparision between different data types.

## `compare` Module

Functions to compare two entries with each other. This is used when generating matches to decide if they match. The function is selected in the config using the `matching.score_func` key.

For more information see [compare/](compare)

## `prepare` Module

Prepares the dataset by generating tokens from the entry's phrases using terminology providers. This is enabled in the config using `matching.calculate_token` and set `matching.compare_column` accordingly.

For more information see [prepare/](prepare)

## `terminology` Module

Providers to access data from different terminology systems to get all matching entries for a single term. The providers are initailized using configuration in `prepare.terminology`.

For more information see [terminology/](terminology)

## `test` Module

Unit test cases

## `types` Module

Holds all the different data classes ranging from `dataset_definition` to `mapping`. Information is read or computed and stored in one of these classes. They also provide the functionality to convert or generate other information and file input and output.

For more information see [types/](types)
