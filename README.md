## Pandas DataFrame Comparison

#### Creates an interactive html report comparing two pandas dataframes, focusing attention on magnitude of difference.  Some of the functionality:
1. Compares column sets for overlap
2. Compares data types for overlapping columns
3. Optionally compares ID columns for uniqueness and overlapping values
4. Outputs df's with summary metrics for each input df
5. Calculates distributional measures for overlapping columns and sorts by magnitude of difference (e.g. KS)
6. Uses Jinja and jQuery to create interactive html report from Python output


#### Potential use cases:
1. Model Development - comparing multiple development and/or scoring samples to understand sources of differences in input distribution
2. Monitoring and Reporting - quickly sorting through lots of data from repeated sampling (e.g. quarterly reports) to focus on interesting changes