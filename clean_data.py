import os, re
import numpy as np
import pandas as pd

filename = 'private_repo/clean_data/new_jewelry_cleaned.csv'

if os.path.exists(filename):
    os.remove(filename)

MATERIALS = ['brass', 'silver', 'gold', 'crystal', 'steel', 'calfskin', 'stainless', 'glass', 'metal',
             'bronze', 'ruby', 'onyx', 'leather', 'pearls', 'leather']

def find_material(row):
    for material in MATERIALS:
        if material in row:
            return row.title()
    return None

def get_details(detail):
    color, material, country, additional = None, None, None, None
    
    if '<br>' not in detail:
        return color, material, country, None
    
    for row in detail.split('<br>'):
        row = row.lower()
        
        if 'color' in row or 'colour' in row:
            if color is None:
                color = row.replace('color', '').replace('colour', '').strip().title()
        elif 'made in' in row:
            if country is None:
                country = row
        else:
            if material is None:
                material = find_material(row)
            else:
                additional = row
    
    return color, material, country, additional


def fix_vendors(x):
    x = x.lower()
    
    if 'moncler basic' in x:
        x = 'moncler'
    
    if 'self portrait' in x:
        x = 'Self-Portrait'
    
    if 'mm6' in x:
        return 'MM6 Maison Margiela'

    if 't shirt' in x:
        return 'T-Shirt'
    
    if 'comme de garcons' in x:
        return 'Comme Des Garçons'
    
    if 'carhartt wip' in x:
        return 'Carhartt WIP'
    
    if x == '"' or x == "''":
        return ''
    
    if 'golden goose' in x:
        return 'Golden Goose'
    
    return x.title()


def get_sizes(x):
    sizes, quantities = [], []
    
    try:
        # Split the string by ';' to separate each block for Size, Quantity, Price, and Old Price
        for row in x.split(';'):
            # Use regex to find Size, Quantity, Price, and Old Price
            size_match = re.search(r'Size:\s*([^,]+)', row)
            quantity_match = re.search(r'Quantity:\s*([^,]+)', row)
            
            # If matches are found, append the results to the respective lists
            if size_match:
                sizes.append(size_match.group(1).strip())
            if quantity_match:
                quantities.append(quantity_match.group(1).strip())
    
        return sizes, quantities

    except AttributeError:
        return None, None

def get_size_and_fit(tab):
    
    size = height = width = length = append_to_descr = fit = diameter = None
    
    if tab == 'ONE SIZE':
        return 'OS', height, width, length, append_to_descr, 'OS', diameter
    
    if tab is None or type(tab) is float or '<br>' not in tab:
        return size, height, width, length, append_to_descr, fit, diameter
    
    append_to_descr = []
    
    for row in tab.split('<br>'):
        row = row.lower()
        
        if 'standard' in row or 'one size' in row:
            if size is None and fit is None:
                if 'standard' in row:
                    size = 'S,M,L'
                    fit  = 'STANDARD'
                else:
                    size = 'OS'
                    fit = 'OS'
        elif 'width' in row and 'pedant' not in row and 'pendant' not in row:
            width = row.replace('width', '').strip().replace(',', '.')
            
            if 'or' in width:
                pass
            else:
                width = re.findall(r'\d+\s*cm', width)[0]
        elif 'length' in row and 'pedant' not in row and 'pendant' not in row:
            length = row.replace('length', '').strip().replace(',', '.')
            
            if 'or' in length:
                pass
            else:
                length = re.findall(r'\d+\s*cm', length)[0]
        elif 'height' in row and 'pedant' not in row and 'pendant' not in row:
            height = row.replace('height', '').strip().replace(',', '.')
            
            if 'or' in height:
                pass
            else:
                height = re.findall(r'\d+\s*cm', height)[0]
        elif 'diameter' in row and 'internal' not in row and 'exterior' not in row and 'interior' not in row:
            diameter = row.replace('diameter', '').strip().replace(',', '.')
        else:
            append_to_descr.append(capitalize_first_letter(row))
            
    append_to_descr = '<br>'.join(append_to_descr) if len(append_to_descr) > 0 else None
    
    return size, height, width, length, append_to_descr, fit, diameter

def round_to_5_or_0(x):
    return np.round(x / 5) * 5

def capitalize_first_letter(sentence):
    if len(sentence) > 0:
        return sentence[0].upper() + sentence[1:]
    return sentence 


def prepare_data():
    data = pd.read_csv('private_repo/clean_data/new_jewelry.csv')
    data.drop_duplicates(inplace=True)
    
    for idx, row in data.iterrows():
        if not row['Retail Price']: continue
        
        title = row['Product Title'].title()
        vendor = fix_vendors(row['Vendor']).upper()
        breadcrumbs = '>'.join(row['Breadcrumbs'].split('>')[1:-1]).strip()
        
        color, material, country, additional_info = get_details(row['Details'])
        color_supplier = color
        accessory_length, accessory_height, accessory_width = None, None, None
        
        if color and '/' in color:
            color = color.split('/')[0].strip().title()
        
        if country:
            country = country.replace('made in', '').strip().title()
            
            if 'Swiss' in country:
                country = country.replace('Swiss', 'Switzerland').title()
                
        if additional_info:
            idx = None
            
            if 'length' in additional_info:
                idx = additional_info.index('length')
                accessory_length = additional_info[idx:].replace('length', '').replace('when open', '').replace('or', '-').strip()
            elif 'width' in additional_info:
                idx = additional_info.index('width')
                accessory_width = additional_info[idx:].replace('width', '').replace('when open', '').replace('or', '-').strip()
            elif 'height' in additional_info:
                idx = additional_info.index('height')
                accessory_height = additional_info[idx:].replace('height', '').replace('when open', '').replace('or', '-').strip()
        
        size, height, width, length, append_to_descr, fit, diameter = get_size_and_fit(row['Size and Fit'])
        
        collection, year = None, None
        
        if row['Collection'] and type(row['Collection']) != float:
            year = '20' + row['Collection'][-2:]
            collection = row['Collection'][:-2].strip()
            collection = '- '.join(collection.split(' ')).title()
        
        sizes, quantities = get_sizes(row['Sizes and Quantities'])

        if sizes:
            
            size_dict = dict(zip(['S', 'M', 'L'], [0] * 3))
            
            s, q = sizes, quantities
            
            # for idx, (k, v) in enumerate(size_dict.items()):
            for idx, s1 in enumerate(s):
                size_dict[s1] = q[idx]
            
            sizes = ','.join([str(x) for x in size_dict.keys()])
            quantities = ','.join([str(x) for x in size_dict.values()])
        
        if not sizes:
            sizes = size
            quantities = 2
        
        
        try:
            retail_price = float(row['Discounted Price'].replace(',', '').replace('€', ''))
            inventory = 'In Stock'
        except AttributeError:
            retail_price = 0
            inventory = 'OUT OF STOCK'
        
        try:
            compare_prices = float(row['Retail Price'].replace(',', '').replace('€', ''))
        except AttributeError:
            if retail_price:
                compare_prices = retail_price
            else:
                compare_prices = 0
                
        if fit is None:
            continue
        
        try:
            retail_price *= 1.08
            compare_prices *= 1.08
            unit_cost = retail_price
            
            retail_price *= 1.25
            compare_prices *= 1.45
            
            retail_price = round_to_5_or_0(retail_price)
            compare_prices = round_to_5_or_0(compare_prices)

            tags = '>'.join(row['Breadcrumbs'].split('>')[1:-1]).strip()
        
            pd.DataFrame({
                'Product Title': [title],
                'SKU': [row['SKU']],
                'Supplier Sku': [row['SKU']],
                'Vendor': [vendor],
                'Tags': [', '.join([breadcrumbs, 'Final Sale', 'exor'])],
                'Color detail': [color],
                'Color Supplier': [color_supplier],
                'Tags': [', '.join([tags, 'Final Sale', 'exor'])],
                'Retail Price': [retail_price],
                'Compare To Price': [compare_prices],
                'Unit Cost': [unit_cost],
                'Year': [year],
                'Season': [collection],
                'Product Category': [tags],
                'Size': [sizes],
                'Qty': [quantities],
                'Inventory': [inventory],
                'Sizing Standard': [fit],
                'Country': [country],
                'Material': [material],
                'Accessory Height': [height.replace('when open', '').replace('or', '-').strip() if height else accessory_height],
                'Accessory Width': [width.replace('when open', '').replace('or', '-').strip() if width else accessory_width],
                'Accessory Length': [length.replace('when open', '').replace('or', '-').strip() if length else accessory_length],
                'Diameter': [diameter],
                'Description': [row['Description'] + '<br>' + capitalize_first_letter(append_to_descr.strip()) if append_to_descr else row['Description']],
                'Clean Images': [row['Images']]
            }).to_csv(filename, index=False, mode='a', header=not os.path.exists(filename))
        except AttributeError:
            print('Missing price for SKU:', row['SKU']) 
            
            
def final_prep():
    prepare_data()
    
    data = pd.read_csv('private_repo/clean_data/new_jewelry_cleaned.csv')
    all_skus = pd.read_csv('private_repo/clean_data/all_skus.csv')
    
    # get products to add
    to_add = data[~data['SKU'].isin(all_skus['SKU'])]
    to_add.to_csv('private_repo/clean_data/to_create.csv', index=False)
    
    # to update
    data.to_csv('private_repo/clean_data/to_update.csv', index=False)
    
    # add new SKUs
    if len(to_add) > 0:
        all_skus = pd.concat([all_skus['SKU'], to_add['SKU']], ignore_index=True)
        all_skus.to_csv('private_repo/clean_data/all_skus.csv', index=False)
    
    all_skus = pd.read_csv('private_repo/clean_data/all_skus.csv')
    
    # get zero inventory
    zero_inventory = all_skus[~all_skus['SKU'].isin(data['SKU'])]
    zero_inventory.to_csv('private_repo/clean_data/zero_inventory.csv', index=False)
    