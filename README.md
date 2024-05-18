# greatbrowser v1.0.2
A selenium implementation in python for Stanford's GREAT browser, allowing for quick and easy genomic analysis.

This repository can be installed as a module

```
pip install greatbrowser
```

with the available functions being accessible though

```
from greatbrowser import great_analysis, great_global_controls, great_get_options
```

A guide demonstrating how these functions may be used is available in the "tests" folder (see: "sample_usage")

The user experience is primarily built around a single function, great_analysis(), with the complementary functions great_get_options() and great_global_controls()
providing context regarding some of the parameters for this function.

The current version supports the ability to find gene associations using probe sets as well the ability to download any GREAT-generated table or plot in dataframe form. 
UCSC genome browser implementation is also supported. Customizability is controlled through parameter tuning, some of which are specific, 
while others are encapsulated within the "global_settings" dictionary parameter as key options. More specific information is available in the great_analysis() docstring. 
Because the project uses switch statements, its requires python >= 3.10 to run.

This repository is ideal for individuals attempting to conduct many different analyses using GREAT across many different probe sets. 
It is fully functional with regards to its ability to modify table output settings, 
but is not ideal if one desires to perform highly custom visual modifications to specifically the raw barplot or hierarchy plots generated by GREAT. 

This repository is not affiliated with the official GREAT browser and was developed solely for the sake of convenience. 

