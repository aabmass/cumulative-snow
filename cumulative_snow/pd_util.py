from typing import Tuple

import pandas as pd


def unzip_mean_and_std(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Separate out the 'mean' and 'std' MultiIndex columns from agg'd group by

    Separates out a MultiIndex data frame where the first level is the
    original columns and the second level is the 'mean' and 'std' columns.
    This format is created by grouping and agg'ing dataframe e.g.:

    >>> df = pd.DataFrame({
    >>>     "a": [3, 2, 1, 0],
    >>>     "b": [5,2,1,1],
    >>>     "year": [2000, 2001, 2000, 2001],
    >>> })
    >>> df_stats = df.groupby("year").agg(['mean', 'std'])
            a              b          
         mean       std mean       std
    year                              
    2000    2  1.414214  3.0  2.828427
    2001    1  1.414214  1.5  0.707107

    This function separates out the mean and std into separate dataframes:

          a    b
    year        
    2000  2  3.0
    2001  1  1.5
                 a         b
    year                    
    2000  1.414214  2.828427
    2001  1.414214  0.707107
    """
    df_mean = pd.DataFrame(index=df.index)
    df_std = pd.DataFrame(index=df.index)

    for col in df.columns.levels[0]:
        df_mean[col] = df[col]["mean"]
        df_std[col] = df[col]["std"]

    return df_mean, df_std
