def great_global_controls():
    '''
    gives information regarding potential "global control" param dictionary keys.\
    this works using the HTML ID, so technically you could modify other things as well, but this is not suggested

    return: none
    '''

    print('Global Control Keys: Input = GREAT Label:\n')
    print('minFold = Minimum Region-based Fold Enrichment:\tint')
    print('n_gene_hits or minAnnotFgHitGenes = Observed Gene Hits:\t int')
    print('filterText = Term Name Filter:\tstr')
    print('allMinAC = Term Annotation Count Min:\tint')
    print('allMaxAC = Term Annotation Count Max:\tint')
    print('sigValue = Statistical Significance Threshhold:\tfloat')
    print('view = Significance view:\tviewSigByBoth, viewSigByRegion, viewFull')

    return

if __name__ == "__great_global_controls__":
  great_global_controls()
