# Rules grammar

Rules has the following format

```
domain:type operator value
```

## Rule elements

### domain

`bach` supports several built-in domains:

* `ads` - get data from Google Ads.
* `youtube` - get data from YouTube Data API.
* `file` - get data from a file.
* `bq` - get data from BigQuery table.
* `sql` - get data from a SqlAlchemy supported DB.

!!! note
    You can omit `ads` domain for Google Ads specific rules.

### type

`type` of the expression can be either a dimension or a metric from a given domain.

i.e. for `ads` domain it can be `clicks` or `campaign_name`

/// tab | clicks
```
ads:clicks > 10
```
///
/// tab | campaign_name
```
ads:campaign_name contains brand
```
///

### operator

Supported operators:

* Arithmetic operators (`>`, `<`, `>=`, `<=`, `=`, `!=`)
* Regular expressions `regexp`
* Other:
    * `is_empty`
    * `not_empty`
    * `contains`
    * `is_ascii`

### value

Depending on selected domain need to specify the `value`.


!!! note
    `value` can be empty for operators `is_empty`, `not_empty`


## Chaining rules

### AND conditions


```
clicks > 10 AND impressions > 100
```

```
clicks > 10,impressions > 100
```

### OR conditions

```
clicks > 10 OR impressions > 100
```

```
clicks > 10;impressions > 100
```
