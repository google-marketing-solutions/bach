`bach` provides an easy to use set of abstractions to simplify
developing Google Ads solutions related to Google Ads management.
Most of the solutions consist of three phases:

* Extract some data
* Do some transformation
* Do something with transformed data

`bach` solves first two generically by simplifying fetching data and applying filtering rules to the fetched data;
the third step is defined as an interface developers can use to build on top of it.

Responsible for orchestrating rules and applying complex rules in Google Ads.
Consists of 3 elements:

* **Rule to Query** - takes complex rules and build GAQL query out of it; query is executed and returned as a `Report`.
* **Rule to Report** - applies Rule to Report to get a subset of actionable entities.
* **Report to Action** - does whatever needs to be done with the subset of data (notification, exclusion, increase / decrease).


## Process

* Takes area and rule
* Builds query and sends to APIs
* Applies rule to results of API calls
* Applies changes in APIs
