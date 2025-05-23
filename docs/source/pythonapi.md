# Python API

The PDG Python API provides a high-level tool for programmatically accessing PDG data.
For most users, this is the recommended way to access PDG data in machine-readable format.
The Python API provides straightforward navigation from particles to
their properties and the corresponding information included in the *Review of Particle Physics*.
After installation the Python API does not require an Internet connection.

The Python API is implemented in Python package [pdg](https://pypi.org/project/pdg/) and uses
a [PDG database file](schema.md) as its default data repository.
The database file corresponding to the current edition of the *Review of Particle Physics*
at the time of releasing a given version of the package is installed together with the package.
When the *Review of Particle Physics* is updated, a new version of the `pdg`
package with the latest data is released.

To access the data from other editions, additional database files can be downloaded from the
[PDG website](https://pdg.lbl.gov/api) and used with the Python API. 
Since [SQLAlchemy](https://www.sqlalchemy.org/) is used for all database access,
the necessary database tables could be copied from the SQLite database file into an existing database
system (as long as it is supported by SQLAlchemy), and the Python API could then be used with that database system.

The `pdg` package is released as open source software and can be found at
[github.com/particledatagroup/api](https://github.com/particledatagroup/api).


## Requirements

The PDG Python API supports Python 3 and requires SQLAlchemy version 1.4 or greater.
For the time being, Python 2.7 is still supported.

## Tutorial

A Jupyter notebook with a comprehensive tutorial on how to use the PDG Python API is [available on github](https://github.com/particledatagroup/api/blob/main/examples/tutorial.ipynb). 

## Installation

The PDG Python API can be installed like any other Python package available from PyPI.

For example, the following commands will first create and activate a Python 3 virtual environment using `venv`
and then download and install package `pdg` and its dependencies:
```
python3 -m venv pdg.venv
source pdg.venv/bin/activate
python -m pip install pdg 
```
(Use `virtualenv` instead of `venv` for Python versions below 3.3.)

If a Python virtual environment was already activated, only the following command is needed: 
```
python -m pip install pdg
```

Alternatively, to add the `pdg` package to one's system Python installation if the system Python
installation is not marked as being externally managed (if it is, there will be an error message
`error: externally-managed-environment`), one can use
```
python -m pip install --user pdg
```


## Usage

Any use of the PDG Python API starts with importing the package and connecting the API to a database file:
```python
import pdg
api = pdg.connect()
```
As discussed below, `connect()` takes two optional arguments:
1. The URL of the database to use. The default is to use the SQLite database file installed with the `pdg` package.
2. Whether the API should operate in pedantic mode or not. Pedantic mode is disabled by default.

### Connecting to a different database
To connect e.g. to a SQLite database file `pdgall-2023-v0.1.sqlite`, which was downloaded from the
[PDG website](https://pdg.lbl.gov/api) into the current directory, one would use
```python
api = pdg.connect('sqlite:///pdgall-2023-v0.1.sqlite')
```

### Pedantic mode

Given the nature of the PDG dataset, there are many special cases and sometimes additional knowledge is needed to
determine the correct answer. For example, when asking for the mass of the top quark, in most cases the mass resulting
from direct measurements is expected, but sometimes the user may want the mass determined from cross-section
measurements. By default, if the user asks for a single value (rather than an iterable over all values),
the API will either make an assumption that is expected to be correct in most cases, or simply return the value listed first
in the Summary Tables or Particle Listings. If this default behaviour is not desirable, the API can connect in
pedantic mode to the database:
```python
api = pdg.connect(pedantic=True)
```
Then, rather than making assumptions in cases where the answer is ambiguous, a `PdgAmbiguousValueError` will be raised.
Thus, taking the example above of the top quark mass,
```python
pdg.connect().get_particle_by_name('t').mass
```
will return a value of about 173 GeV (2024 edition), while
```python
pdg.connect(pedantic=True).get_particle_by_name('t').mass
```
will raise `pdg.errors.PdgAmbiguousValueError: Ambiguous best property for t mass (Q007/2024)`.


### Getting information about the database being used

After connecting to a database, the API object can be printed for a summary of edition, citation, versions and license
information. These and more quantities (see `api.info_keys()`) can be accessed as properties of the API object or by
using `api.info(key)`. For example
```python
api.edition
```
provides the edition (publication year) of the *Review of Particle Physics* from which the data is taken.

### Navigation

Unless the [PDG Identifier](pdgidentifiers.md) of the quantity of interest is known, one will generally retrieve
the information for the desired particle and then navigate to the properties of interest. Particles can be
retrieved by their ASCII name, Monte Carlo particle number, or PDG Identifier. For example, the following three
statements each retrieve the data for the Higgs particle:
```python
by_name = api.get_particle_by_name('H')
by_mcid = api.get_particle_by_mcid(25)
by_pdgid = api.get('S126')[0]
```
Note that `api.get(PDGID)` returns an object of the most appropriate type for the PDG Identifier requested.
If the PDG Identifier denotes a particle, a `PdgParticleList` is returned, which is a list of all the particle's charge
states included under that PDG Identifier. For example, `S008` is the PDG Identifier for charged pions and hence
```python
[p.name for p in api.get('S008')]
```
returns `['pi+', 'pi-']`.

In addition, one can iterate over all particles using `api.get_particles()`, and
`api.get_all()` allows to iterate over all PDG Identifiers, optionally specifying to iterate only over identifiers
referring to a particular type of data such as mass. For example, the following complete code snippet will print
the list of all PDG Identifiers with their descriptions:
```python
import pdg
api = pdg.connect()
for item in api.get_all():
  print('%-20s  %s' % (item.pdgid, item.description))
```


## Examples

After retrieving the desired particle, one can then either directly get the desired quantity such as particle mass
or quantum numbers, or obtain an iterator over the desired information such as all exclusive branching fractions
for which PDG has data. A few examples with complete code snippets are given below.

### Particle Monte Carlo number, mass and quantum numbers

_Note: The Monte Carlo particle numbering scheme was substantially updated
and extended in 2012. The Python API follows the particle numbering used in the current version of the
[PDG table of particle information](https://pdg.lbl.gov/2024/mcdata/mass_width_2024.txt) where certain excited
baryons follow the pre-2012 scheme. A further revision and/or extension of the numbering scheme is anticipated 
in the near future._

The following code snippet could be used to print the Monte Carlo particle number, mass (without rounding or errors),
and spin of the negative pion:
```python
import pdg
api = pdg.connect()
pi_minus = api.get_particle_by_name('pi-')
print('MC ID  = ', pi_minus.mcid)
print('mass   = ', pi_minus.mass, 'GeV')
print('spin J = ', pi_minus.quantum_J)
```

### Properties and measurements

The following code snippet iterates over the mass properties of the top quark.
For each property, the best summary value is printed, followed by all individual
measurements included in PDG fits or averages:

```python
import pdg
api = pdg.connect()
for mass in api.get_particle_by_name('t').masses():
    print('Best summary value for %s (%s): %s = %s'
          % (mass.pdgid, mass.description, mass.best_summary().value_type,
             mass.best_summary().value_text))
    for msmt in mass.get_measurements():
        if msmt.get_value().used_in_average or msmt.get_value().used_in_fit:
            print('%s (%s): %s'
                  % (msmt.reference.doi, msmt.reference.title,
                     msmt.get_value().value_text))
    print()
```

For a more extensive example, see `examples/print_datablock.py` in the API
repository.

### Branching fractions

The following code snippet prints all exclusive branching fractions of the charged B meson with their description,
'True' if the value denotes a limit, and the raw value (as an unrounded floating point number or None).
```python
import pdg
api = pdg.connect()
for bf in api.get_particle_by_name('B+').exclusive_branching_fractions():
    print('%-60s    %4s    %s' % (bf.description, bf.is_limit, bf.value))
```

### Decays

For branching fractions one can access the particles in the corresponding decay as a list of decay products (`PdgDecayProduct`).
Each `PdgDecayProduct` specifies the item (`PdgItem`) that appears, a multiplier, and whether the item needs to decay
in a specific way. `PdgItems` can represent a particle of a specific charge (e.g. a pi+), a generic particle such
as a kaon without specifying its charge, a lepton (which could be either an electron or a muon), or a textual description
such as ">= 0 neutrals".

In a simple case, all decay products appear with multiplicity 1 and are particles with specified charge. For example:
```python
pion_decay = api.get('S008.1')
pion_decay.description                            # 'pi+ --> mu+ nu_mu'
len(pion_decay.decay_products)                    # 2
pion_decay.decay_products[0].multiplier           # 1
pion_decay.decay_products[0].item.name            # 'mu+'
pion_decay.decay_products[0].item.particle.mcid   # -13 
```

By querying the decay products one can easily filter out specific decay modes. For example, the following code snippet
prints all exclusively measured B0 decays that produce a J/psi:
```python
import pdg
api = pdg.connect()

for decay in api.get_particle_by_name('B0').exclusive_branching_fractions():
    decay_products = [p.item.name for p in decay.decay_products]
    if 'J/psi(1S)' in decay_products:
        print(format(decay.description,'40s'), decay.display_value_text)
```

### Particle properties (except branching fractions)

The following code snippet prints all properties other than branching fractions of the charged pion (retrieved this
time via Monte Carlo number rather than name). For each property, the PDG Identifier, the description, and the
rounded value with error is shown.
```python
import pdg
api = pdg.connect()
for p in api.get_particle_by_mcid(211).properties():
    print('%16s:  %-60s    %s' % (p.pdgid, p.description, p.display_value_text))
```



## Detailed software documentation

Detailed information on all public classes, methods and utility functions provided by the PDG Python API
is given below, based on the inline code documentation.

```{eval-rst}
.. include:: pdg.rst
```

## License

The data obtained from the PDG Python API is subject to the license used by the corresponding edition
of the _Review of Particle Physics_.
Starting with the 2024 edition, the _Review of Particle Physics_ is published under a
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) license.
