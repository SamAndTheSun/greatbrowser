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
        try: bed_data = pd.read_excel(bed_data)
        except: bed_data = pd.read_csv(bed_data)

    #format df
    if isinstance(bed_data, pd.DataFrame) or isinstance(bed_data, pl.DataFrame):

        bed_data[df_start] = bed_data[df_start].astype(int)
        bed_data[df_end] = bed_data[df_end].astype(int)

        n = 0
        if isinstance(bed_data, pd.DataFrame) or isinstance(bed_data, pl.DataFrame):
            while n < bed_data.shape[1]: #get appropriate columns
                try: df_dict[potential_cols[n]] = bed_data[potential_cols[n]]
                except: pass
                n+=1
        elif isinstance(bed_data, np.ndarray):
            while n < bed_data.shape[1]: #get appropriate columns
                try: df_dict[potential_cols[n]] = bed_data[:, n]
                except: pass
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

    #add _ to all indices to differentiate them from genes in parsing
    bed_data[df_index] = bed_data[df_index].astype(str)   
    bed_data[df_index] = bed_data[df_index] + '_'

    return bed_data

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
        if '_' in tag.text: #differentiate between indices and values
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
