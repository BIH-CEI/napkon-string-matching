# `napkon_string_matching.terminology` Module

Provides multiple classes to provide information from different terminologies. There are providers for each terminology and a `TerminologyProvider` that combines the data from mutiple providers.

There are different providers that implement `ProviderBase`. Each of them provide matches for a term for a terminology. They return a list of matched terms and their IDs.

Additionally, there is `TerminologyProvider` that allows to access multiple terminologies using a single interface.
