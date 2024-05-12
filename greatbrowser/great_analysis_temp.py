def great_get_options():
    '''
    gives information regarding potential "get" parameter options.\
        for more in-depth information about each particular output, see https://great-help.atlassian.net/wiki/spaces/GREAT/overview'
    return: none
    '''
        
    print('"get" Parameter Options:\n')
    print('get = genes \t returns a dataframe of the inputted data + genes associated with each probe. For large datasets, run multiple iterations and merge dataframes post-hoc using pd.concat')
    print('get = ucsc_browser \t opens ucsc genome browser for the inputted data')
    print('get = genes_pivot \t same as genes, but grouped by gene rather than region')
    print('get = n_genes_region \t saves a barplot showing the number of region with x gene associations, grouped by x, as a png')
    print('get = n_genes_TSS \t saves a batplot showing the distance between each probe/gene pair, grouped by kilobases, as a png')
    print('get = n_genes_abs_TSS \t same as n_genes_TSS but with absolute value being used for distance')

    print('\nThe below options all additionally save a png if plot=bar (barplot) or plot=hierarchy (hierarchy plot) (default=False)\n')

    print('get = ensembl_genes \t returns a dataframe of the Ensembl genes processes associated with the probe set')
    print('get = go_process \t returns a dataframe of the GO biological processes associated with the probe set')
    print('get = go_component \t returns a dataframe of the GO cellular components associated with the probe set')
    print('get = go_function \t returns a dataframe of the GO molecular functions associated with the probe set')
    print('get = human_phenotype \t returns a dataframe of the human phenotypes associated with the probe set')
    print('get = mouse_phenotype \t returns a dataframe of the mouse phenotypes associated with the probe set')
    print('get = mouse_phenotype_KO \t returns a dataframe of the mouse phenotypes associated with knock out of the probe set')
    

    print('\nFor more advanced information regarding the interpretation and calculation of the available outputs, see https://great-help.atlassian.net/wiki/spaces/GREAT/overview')
    
    return

if __name__ == "great_get_options":
  great_get_options()
