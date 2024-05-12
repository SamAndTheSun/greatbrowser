from selenium import webdriver
from bs4 import BeautifulSoup

import requests

from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait, Select

from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, WebDriverException

import os
import pandas as pd
pd.options.mode.chained_assignment = None

import polars as pl
import numpy as np
from PIL import Image
import io

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def format_for_great(bed_data: pd.DataFrame | pl.DataFrame | list | np.ndarray | str, df_chr, df_start, df_end, df_index,
                     df_score, df_strand, df_thickStart, df_thickEnd, df_rgb):
    '''
    formats the inputted data so that it is processed properly by GREAT

        param bed_data: the data to be assessed. The data is converted into a dataframe with the columns "chr", "start", "end", and "name"
            If there are enough columns, score, strand, thickStart, thickEnd, and rgb are also made into columns
        param df_chr: the name of the column in bed_data representing chromosome
        param df_start: the name of the column in bed_data representing start point
        param df_end: the name of the column in bed_data representing end point
        param df_index: the name of the column in bed_data representing name, or index
        param df_score: the name of the column in bed_data representing score
        param df_strand: the name of the column in bed_data representing start point
        param df_thickStart: the name of the column in bed_data representing thickStart
        param df_thickEnd: the name of the column in bed_data representing thickEnd
        param df_rgb: the name of the column in bed_data representing rgb

        return: bed formatted df
    '''

    #precursors for dataframe construction
    potential_cols = [df_chr, df_start, df_end, df_index, df_score, df_strand, df_thickStart, df_thickEnd, df_rgb]
    df_dict = {}

    #convert list to np array
    if isinstance(bed_data, list):
        bed_data = np.array(bed_data)

    #load file as df
    elif isinstance(bed_data, str):
        bed_data = pd.read_excel(bed_data)

    #format df
    if isinstance(bed_data, pd.DataFrame) or isinstance(bed_data, pl.DataFrame):

        n = 0
        if isinstance(bed_data, pd.DataFrame) or isinstance(bed_data, pl.DataFrame):
            while n < bed_data.shape[1]: #get appropriate columns
                df_dict[potential_cols[n]] = bed_data.iloc[:, n]
                n+=1
        elif isinstance(bed_data, np.ndarray):
            while n < bed_data.shape[1]: #get appropriate columns
                df_dict[potential_cols[n]] = bed_data[:, n]
                n+=1
        if n < 4: #if there's no index, add one:
            df_dict[potential_cols[n]] = [x for x in range(len(df_dict[potential_cols[n-1]]))]

        bed_data = pd.DataFrame().from_dict(df_dict)

        #mandatory inputs
        if potential_cols[0] not in df_dict: raise Exception(f'KeyError: "{df_chr}" not found in columns')
        if potential_cols[1] not in df_dict: raise Exception(f'KeyError: "{df_start}" not found in columns')
        if potential_cols[2] not in df_dict: raise Exception(f'KeyError: "{df_end}" not found in columns')

    else:
        print('Invalid file type detected. Must be either pandas dataframe, polars dataframe, list, numpy array, or path (str)')

    return bed_data

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

def get_genes(driver):
    '''
    get the gene table for a given region set
        param driver: the driver focused on the webpage of interest

        return: list of lists containing genes by id
    '''

    #show the gene associations
    show_table_button = driver.find_element(By.LINK_TEXT, 'View all genomic region-gene associations.')
    show_table_button.click()

    while True:
        try:
            #Load the gene association data
            driver.switch_to.window(driver.window_handles[1]) #focus driver on newly opened tab
            break
        except IndexError: pass

    #Find the relevant gene table
    try:
        soup = BeautifulSoup(driver.page_source, 'lxml')
        tables = soup.find_all('table', class_='gSubTable')
    except WebDriverException:
        raise Exception('Error: Loading exceeded 1 minute. Potential reasons: dataset too large for GREAT or connection problems. To get gene associations for large datasets, split the dataset first. Use headless=False to troubleshoot')

    #Find all gene names and positions
    gene_tags = tables[0].find_all('td')

    #prepare to create list of genes from table
    gene_by_ids = []
    gene_list = []

    #Extract gene names / positions by id
    for tag in gene_tags:
        if ('+' not in tag.text) and ('-' not in tag.text): #differentiate between indices and values
            gene_by_ids.append(gene_list)
            gene_list = []
        else:
            gene_list.append(tag.text)
    
    return gene_by_ids

def get_genes_pivot(driver):
    '''
    get the region table for a given gene set
        param driver: the driver focused on the webpage of interest

        return: list of lists containing ids by gene
    '''

    gene_list = []
    id_list = []
    
    #show the gene associations
    show_table_button = driver.find_element(By.LINK_TEXT, 'View all genomic region-gene associations.')
    show_table_button.click()

    #Load the gene association data
    driver.switch_to.window(driver.window_handles[1]) #focus driver on newly opened tab

    #Find the relevant gene table
    try:
        soup = BeautifulSoup(driver.page_source, 'lxml')
        tables = soup.find_all('table', class_='gSubTable')
    except WebDriverException:
        raise Exception('Error: Loading exceeded 1 minute. Potential reasons: dataset too large for GREAT or connection problems. To get gene associations for large datasets, split the dataset first. Use headless=False to troubleshoot')

    #Find all gene names and positions
    gene_tags = tables[1].find_all('td')
    genes = gene_tags[::2]
    ids = gene_tags[1::2]

    for g, i in zip(genes, ids):
        gene_list.append(g.text)
        id_list.append(i.text)

    gene_pivot = pd.DataFrame({'genes' : gene_list, 'ids' : id_list})

    return gene_pivot

def get_ucsc_browser(driver):
    '''
    send the region set to ucsc browser, and open this in a new window
        param driver: the driver focused on the webpage of interest

        return: none
    '''

    #click the ucsc browser link
    driver.execute_script("window.scrollTo(0, 0);")
    go_to_ucsc_btn = driver.find_element(By.LINK_TEXT, 'Show in UCSC genome browser.')
    driver.execute_script("arguments[0].click();", go_to_ucsc_btn)

    #switch to ucsc browser tab
    driver.switch_to.window(driver.window_handles[1])

    #wait for the browser to load, then get the url
    try: newelem = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'assemblyName')))
    except TimeoutException: raise Exception('Error: Loading exceeded 10 seconds. Potential reason: connection problems. Use headless=False to troubleshoot.')
    new_driver = driver.current_url

    #establish settings for new driver
    new_options = Options()
    new_options.add_argument('--disable-dev-shm-usage')
    new_options.add_experimental_option('detach', True)


    #establish driver
    new_driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()),
                            options=new_options)
    
    new_driver.get(driver.current_url)
    driver.quit()

    return

def get_n_genes_region(driver, specifier, file_name, get):
    '''
    download a plot indicating the distance between the regions and their associated genes

        param driver: the driver focused on the webpage of interest
        param specifier: specifies which plot to download. 0 refers to the number of associated genes per region,\
            1 refers to this binned by orientation and distance from TSS, and 2 is the same as 1, but uses absolute distance
        param file_name: the name of the outputted image file, excluding file extension
        param get: determines the file name if none is specified via file_name

        return: none   
    '''

    #get all images, then select appropriate figure
    img_elements = driver.find_elements(By.TAG_NAME, 'img')
    img_element = img_elements[specifier+6]

    #determine plot name
    if file_name == None: 
        file_name = get
    #get figure
    img_url = img_element.get_attribute('src')
    response = requests.get(img_url, verify=False)

    #add white background to image (transparent by default)
    img = Image.open(io.BytesIO(response.content))
    img = img.convert('RGBA')
    new_img = Image.new('RGB', img.size, (255, 255, 255))
    new_img.paste(img, (0, 0), img)

    #save image to working directory
    new_img.save(f'{file_name}.png')
    print(f'Image saved as {file_name}.png in {os.getcwd()}')

    return

def get_table(driver, specifier):
    '''
    get a table of data from GREAT, depending on which table is specified

        param driver: the driver focused on the webpage of interest
        param specifier: specifies which table to download. more information can be ascertained by calling great_get_options()

        return: specified table   
    '''

    while True: #account for serverside issues

        #get data from tables
        try:
            soup = BeautifulSoup(driver.page_source, 'lxml')
            tables = soup.find_all('table', class_='gSubTable')
        except WebDriverException: raise Exception('Error: Loading exceeded 1 minute. Potential reasons: dataset too large for GREAT or connection problems. To get gene associations for large datasets, split the dataset first. Use headless=False to troubleshoot')
        soup = BeautifulSoup(driver.page_source, 'lxml')

        #Find the relevant table
        tables = soup.find_all('table')
        table = tables[specifier]

        # Iterate through each row of the table
        rows = table.find_all('td')
        if 'No results meet your chosen criteria.' in str(rows):
            print('No results meet your chosen criteria.')
            return -1

        all_row_info = []
        row_info = []
        n = 0
        for cell in rows:

            if n == 22:
                try: row_info.remove('Loading...')
                except ValueError: pass

                all_row_info.append(row_info)
                row_info = []
                n = 1

            b = cell.find('b')
            div = cell.find('div')
            if b: row_info.append(b.text)
            else: row_info.append(div.text)

            n+=1

        if all_row_info == []:
            pass
        else:
            break

    column_names = ['term_name','go_annotation','binom_rank','binom_raw_pval','binom_bonferroni_pval',
               'binom_fdr_qval','binom_fold_enrichment','binom_expected','binom_obs_region_hits',
               'binom_genome_fraction','binom_region_set_coverage', 'hyper_rank','hyper_raw_pval','hyper_bonferroni_pval',
                'hyper_fdr_qval','hyper_fold_enrichment','hyper_expected','hyper_obs_gene_hits', 
                'hyper_total_genes','hyper_gene_set_coverage', 'hyper_term_gene_coverage']
    table_df = pd.DataFrame.from_records(all_row_info, columns=column_names)
        
    return table_df

def adjust_global_controls(driver, to_adjust : dict):
    '''
    modifies "global control" parameters

        param driver: the driver focused on the webpage of interest
        param to_adjust: dictionary determining which parameters are adjusted. takes id as input and desired value as output.\
            see great_global_controls() for more information

        return: none
    '''

    #expand global controls table
    driver.execute_script("document.getElementById('global_controls_container').style.display = 'block';")

    #because original id is wordy
    if 'n_gene_hits' in to_adjust:
        driver.find_element(By.ID, 'minAnnotFgHitGenes').send_keys('value', to_adjust['n_gene_hits'])
        to_adjust.pop('n_gene_hits')

    #change the selected pval view
    if 'view' in to_adjust:
        switch_pval_view = driver.find_element(By.ID, to_adjust['view'])
        switch_pval_view.click()
        to_adjust.pop('view')

    #change all other params
    for key in to_adjust.keys():
        driver.find_element(By.ID, key).clear()
        driver.find_element(By.ID, key).send_keys(to_adjust[key])

    #update table
    update_btns_criteria = f'//button[contains(@class, "button") and @value="Set"]'
    update_btns = driver.find_elements(By.XPATH, update_btns_criteria)
    for btn in update_btns: btn.click()

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

def plot_table(driver, plot_type, n, get, file_name):
    '''
    plots the selected table in the selected form, and outputs this as a png

        param driver: the driver focused on the webpage of interest
        param plot_type: the type of plot to generate, utilizing GREAT's built in functionality. options: "bar", "heirarchy"
        param n: the specific table to select for plotting
        param get: the name of the table to plot, excluding extension. replaces file_name functionally when file_name is not provided
        param file_name: the name of the outputted image file, excluding extension

        return: none
    '''

    while True: #necessary due to inconsistencies server side, I think, adding wait time periods changes nothing
        #open correct figure type
        show_list = driver.find_elements(By.CLASS_NAME, 'visList')
        select = Select(show_list[n])

        if plot_type == 'bar': 
            select.select_by_visible_text('Bar chart of current sorted value')
        elif plot_type == 'hierarchy': 
            select.select_by_visible_text('Visualize shown terms in hierarchy')
        else: 
            print('Error: invalid type selected. Valid options include: "bar", "hierarchy"')
        try:
            driver.switch_to.window(driver.window_handles[1])
            break
        except IndexError:
            show_list = driver.find_elements(By.CLASS_NAME, 'visList')
            select = Select(show_list[n])
            select.select_by_visible_text('[select one]')

    #wait until element is available
    if plot_type == 'bar':    
        try: newelem = WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, 'chart_container')))
        except TimeoutException: raise Exception('Error: Loading exceeded 15 seconds. Potential reason: connection problems. Use headless=False to troubleshoot.')
    else: 
        try: newelem = WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, 'svgContainer')))
        except TimeoutException: raise Exception('Error: Loading exceeded 15 seconds. Potential reason: connection problems. Use headless=False to troubleshoot.')

    #set plot name
    if file_name == None:
        file_name = f'{get}_{plot_type}_plot.png'
    else:
        file_name = f'{file_name}.png'

    #wait until element is available
    try: newelem = WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.LINK_TEXT, 'PDF')))
    except TimeoutException: raise Exception('Error: Loading exceeded 15 seconds. Potential reason: connection problems. Use headless=False to troubleshoot.')

    #show download link (hierarchy) or get full size image (bar)
    show_download_link = driver.find_element(By.LINK_TEXT, 'PNG')
    show_download_link.click()

    if plot_type == 'hierarchy': 
        #wait until element is available
        try: newelem = WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.LINK_TEXT, 'click here')))
        except TimeoutException: raise Exception('Error: Loading exceeded 15 seconds. Potential reason: connection problems. Use headless=False to troubleshoot.')

        #get full screen image
        download_link = driver.find_element(By.LINK_TEXT, 'click here')
        download_link.click()
    
    #switch to image tab
    while True: #ditto
        try:
            driver.switch_to.window(driver.window_handles[2])
            break
        except IndexError:
            pass

    #get png
    img = driver.find_element(By.TAG_NAME, 'img')
    src = img.get_attribute('src')
    response = requests.get(src, verify=False)
    
    #write pdf as file
    with open(file_name, 'wb') as f:
        f.write(response.content)

    print(f"PNG image downloaded successfully as '{file_name}'")
    return
