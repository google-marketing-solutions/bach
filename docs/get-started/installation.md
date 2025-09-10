# Installing bach

[![PyPI](https://img.shields.io/pypi/v/bach-googleads?logo=pypi&logoColor=white&style=flat-square)](https://pypi.org/project/bach-googleads)

## Create and activate virtual environment

/// tab | pip
```bash
python -m venv .venv
source .venv/bin/activate
```
///

/// tab | uv
```bash
uv venv
source .venv/bin/activate
```
///

## Installation

/// tab | pip
```python
pip install bach-googleads
```
///

/// tab | uv
```python
uv add bach-googleads
```
///

###  with server support

In order to call `bach-googleads` via API you need install additional dependencies.

/// tab | pip
```python
pip install bach-googleads[server]
```
///

/// tab | uv
```python
uv add bach-googleads[server]
```
///
