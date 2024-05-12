from selenium import webdriver

from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, WebDriverException

import os
import pandas as pd
pd.options.mode.chained_assignment = None

import polars as pl
import numpy as np

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from greatbrowser.functions import format_for_great, get_genes, get_genes_pivot, get_ucsc_browser, get_n_genes_region, get_table, adjust_global_controls, plot_table

def great_analysis(test_regions: pd.DataFrame | pl.DataFrame | list | np.ndarray | str, get='genes', assembly='mm10', is_formatted=False, background_regions=False, 
              headless=True, df_chr='chr', df_start='start', df_end='end', df_index='index', df_score='score', 
              df_strand='strand', df_thickStart='thickStart', df_thickEnd='thickEnd', df_rgb='rgb', assoc_criteria='basal', cur_reg=True, 
              plot = False, file_name = None, global_controls = dict):
    '''
    uses the given data sets to conduct automated analysis using GREAT browser

        param test_regions: the test data to be assessed. Used to determine which regions are selected
        param get: determines what information is generated by the function. for more information call great_get_options()
        param assembly: the assembly of the inputted region set. Valid options include: hg38, hg19, mm10, mm9\
            For other assemblies consider the 'liftover' module. Not suggested for rs data
        param is_formatted: whether the inputted test and background regions are already formatted (i.e. whether formatting should be applied or not)
        param background_regions: the background data to be assessed. Must be a superset including the test set
        param headless: determines whether the browser is shown during operation or not. overridden for certain get options
        param df_chr: the name of the column in bed_data representing chromosome
        param df_start: the name of the column in bed_data representing start point
        param df_end: the name of the column in bed_data representing end point
        param df_index: the name of the column in bed_data representing name, or index
        param df_score: the name of the column in bed_data representing score
        param df_strand: the name of the column in bed_data representing start point
        param df_thickStart: the name of the column in bed_data representing thickStart
        param df_thickEnd: the name of the column in bed_data representing thickEnd
        param df_rgb: the name of the column in bed_data representing rgb
        param assoc_criteria: the criteria through which genes are associated with regions. options include: "basal", "one_closest", "two_closest"
        param cur_reg: whether or not to include curated regulatory domains\
            see https://great-help.atlassian.net/wiki/spaces/GREAT/pages/655443/Association+Rules#AssociationRules-CuratedRegulatoryDomains for more details
        param plot: whether or not to plot tables for certain get options, detailed in great_get_options(). options include: "bar", "hierarchy"
        param file_name: what to name any pngs downloaded via get options, detailed in great_get_options(). do not include the extension
        param global_controls: dictionary controlling certain attributes of the data analysis. see great_global_controls() for more information
 
        return: varies depending on 'get' parameters. call great_get_options() for more information
    '''

    #format genetic data if not already formatted
    if not is_formatted:
        test_regions = format_for_great(test_regions, df_chr, df_start, df_end, df_index, df_score, df_strand, df_thickStart, df_thickEnd, df_rgb)
        if not isinstance(background_regions, bool): 
            background_regions = format_for_great(background_regions, df_chr, df_start, df_end, df_index, df_score, df_strand, df_thickStart, df_thickEnd, df_rgb)
    elif isinstance(test_regions, str): #load formatted file
        test_regions = pd.read_excel(test_regions)
        if not isinstance(background_regions, bool):
            background_regions = pd.read_excel(background_regions)
    
    #establish settings
    options = Options()
    options.add_argument('--ignore-ssl-errors=yes') #ignore insecure warning
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument("--disable-extensions")

    if headless:
        options.add_argument('--headless') #makes it so that the browser doesn't open

    #establish driver
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()),
                            options=options)
    driver.get('https://great.stanford.edu/great/public/html/')

    cookies = driver.get_cookies()
    #get cookies for requests, helps to deal with 403 denied error
    for cookie in cookies:
        driver.add_cookie(cookie)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    
    #set assembly to desired choice
    set_assembly = driver.find_element(By.ID, assembly)
    set_assembly.click()

    #select 'BED data'
    use_input = driver.find_element(By.ID, 'fgChoiceData')
    use_input.click()

    #put BED data into text box
    test_regions_string = test_regions.to_csv(index=False, header=None, sep='\t')
    driver.execute_script('arguments[0].value = arguments[1];', driver.find_element(By.NAME, 'fgData'), test_regions_string)

    #add background region data if applicable
    if isinstance(background_regions, bool): pass
    else:

        #select button to input
        bg_input = driver.find_element(By.XPATH, '/html/body/div[2]/div[4]/div/form/fieldset/div[3]/div/ul/li[3]/label/input')
        bg_input.click()

        #put background data into text box
        background_regions_string = background_regions.to_csv(index=False, header=None, sep='\t')
        driver.execute_script('arguments[0].value = arguments[1];', 
                                driver.find_element(By.XPATH, '/html/body/div[2]/div[4]/div/form/fieldset/div[3]/div/ul/li[3]/textarea'), 
                                background_regions_string)
        
    #show genomic region options
    show_criteria = driver.find_element(By.ID, 'assoc_btn')
    show_criteria.click()

    #select gene association criteria
    if assoc_criteria == 'basal':
        pass
    else:
        #select criteria
        if assoc_criteria == 'two_closest':
            select_criteria = driver.find_element(By.ID, 'twoClosestRule')
            select_criteria.click()
        elif assoc_criteria == 'one_closest':
            select_criteria = driver.find_element(By.ID, 'oneClosestRule')
            select_criteria.click()
        else:
            raise Exception('Invalid criteria given. Valid options include "basal", "two_nearest", and "one_nearest"')

    #change curated regulatory domain option
    if cur_reg:
        pass
    else:
        cur_reg_dom = driver.find_element(By.ID, 'adv_includeCuratedRegDoms')
        cur_reg_dom.click()

    #submit data
    submit = driver.find_element(By.ID, 'submit_button')
    submit.click()

    #wait for the table
    try: newelem = WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.ID, 'job_description_container')))
    except TimeoutException:
        error_msg = driver.find_element(By.XPATH, '/html/body/div[2]/div[2]/blockquote ')
        print(error_msg.text)
        raise Exception('Error: Loading exceeded 1 minute. Potential reasons: invalid input (generally or for assembly) or connection problems. Use headless=False to troubleshoot.')
    
    #expand the table
    driver.execute_script("document.getElementById('job_description_container').style.display = 'block';")

    #modify global controls
    if isinstance(global_controls, dict):
        adjust_global_controls(driver, global_controls)

    #get desired data
    output = False #default output
    n_table = False #default table
    match get:
        case 'genes':
            output = test_regions 
            output['associated_genes'] = get_genes(driver)
        case 'ucsc_browser': get_ucsc_browser(driver) 
        case 'genes_pivot': output = get_genes_pivot(driver)
        case 'n_genes_region': get_n_genes_region(driver, 0, file_name, get)
        case 'n_genes_TSS': get_n_genes_region(driver, 1, file_name, get)
        case 'n_genes_abs_TSS': get_n_genes_region(driver, 2, file_name, get)
        case 'ensembl_genes': n_table = 0; output = get_table(driver, n_table)
        case 'go_process': n_table = 1; output = get_table(driver, n_table)
        case 'go_component': n_table = 2; output = get_table(driver, n_table)
        case 'go_function': n_table = 3; output = get_table(driver, n_table)
        case 'human_phenotype': n_table = 4; output = get_table(driver, n_table)
        case 'mouse_phenotype_KO': n_table = 5; output = get_table(driver, n_table)
        case 'mouse_phenotype': n_table = 6; output = get_table(driver, n_table)

    if not isinstance(output, pd.DataFrame): #if an output does not exist, quit the driver and return
        driver.quit()
        return
    elif not isinstance(n_table, pd.DataFrame) == False: #if a table is not defined, quit the driver and return the output
        pass
    elif not isinstance(plot, str): #if a table is defined, and visualization is not active, quit the driver and return the output
        pass
    else:
        plot_table(driver, plot, n_table, get, file_name)

    driver.quit()
    return output

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

if __name__ == "__main__":
  great_global_controls()
  great_get_options()
  great_analysis()
