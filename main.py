# Burak Şenol

#Selenium WebDriver and BS4
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import requests
from bs4 import BeautifulSoup
import datetime
import pandas as pd
import time
import os
import re
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

#Google Sheets API Conn
import gspread



def google_sheets_initialize():
    # Google Sheets Initialize
    gc = gspread.service_account(filename='credentials.json')
    sh = gc.open_by_key('GoogleSheetsKey(URL)')
    return sh.sheet1


def selenium_initialize():
    DRIVER_PATH = os.path.join(ROOT_DIR, 'chromedriver.exe')
    options = Options()
    options.headless = True
    options.add_argument("--window-size=1920,1200")
    options.add_argument('--headless')
    options.add_argument('--hide-scrollbars')
    options.add_argument('--disable-gpu')
    options.add_argument("--log-level=3")  # uyarıları kapatmak için.
    options.binary_location = "C:\Program Files\Google\Chrome\Application\chrome.exe"
    
    
    return webdriver.Chrome(options=options, executable_path=DRIVER_PATH)


def product_name(self):
    # Product Name
    flag = self.findAll("div", {"id": "productInfo"})
    for element in flag:
        for x in element.findAll("h1"):
            product_n = (x.text).strip()
    
    product_n = product_n.replace("\n", "")
    return product_n


def offer(self):
    # Offer
    flag = self.findAll("div", {"class": "detay-indirim"})
    for element in flag:
        offer_n = element.text
    
    try:
        return offer_n
    except:
        offer_n = None
        return offer_n

def price_list(self):
    # Product_Price and Sale_Price
    flag = self.findAll("div", {"class": "fl priceLine"})
    for element in flag:
        price_list_raw = (element.text).strip()
        price_list_raw = price_list_raw.strip()

    try:
        test = price_list_raw.split("TL")
        p_price = test[0].strip()
        s_price = test[1].strip()
    except:
        p_price = ''
        s_price = ''

    return [p_price, s_price]


def availability(self):
    # Availability
    passive_list = []
    active_list = [] 
    flag = self.findAll("div", {"class": "fl col-12 variantBox subTwo"})
    for element in flag:
        for x in element.findAll("div", {"class": "new-size-variant fl col-12 ease variantList"}):
            for y in x.findAll("a"):
                if 'passive' in y.attrs['class']:
                    passive_list.append(y.text)
                else:
                    active_list.append(y.text)

    return str(int(len(active_list) * 100 / (len(passive_list) + len(active_list)))) + '%'


def product_code_v1(self):
    # Product Code 
    flag = soup.findAll("div", {"class": "product-feature-content"})
    for element in flag:
        # assoc. => https://stackoverflow.com/questions/42195910/python-remove-all-occurrences-until-first-space/42195931
        s = element.text[-25:]

        try:
            product_code = s.split(None, 1)[1]
            if 'ÜRETİM' in product_code:
                product_code = product_code.replace("ÜRETİM", "")
                product_code = product_code.replace(" ", "")
            elif 'Türkiye' in product_code:
                product_code = product_code.replace("Türkiye", "")
                product_code = product_code.replace(" ", "")
            elif ':' in product_code:
                product_code = product_code.replace(":", "")
                product_code = product_code.replace(" ", "")
            
            
            product_code = product_code.replace("\n", "")
        except:
            product_code = None
        
    return product_code
       


if __name__ == '__main__':

    # Initialize the google sheets API and Selenium Driver.
    worksheet = google_sheets_initialize()    
    driver = selenium_initialize()




    df = pd.read_excel(r'url_list.xlsx')
    base = 'https://www.markastok.com'
    sheets_url = []
    prod_name_list = []
    prod_offer_list = []
    prod_price_list = []
    sale_price_list = []
    availability_list = []
    prod_code_list = []
    i = 0
    for prod_url in df['/']:
        # URL Listesi içerisinde rakamsal değer içeren kayıtlar genellikle..
        # product sayfaları oluyor. Bu yüzden REGEX ile içerisinde Rakam olan değerler..
        # product url olarak base_url'e append'lenir.
        if bool(re.search(r'\d', prod_url)):
            
            driver.get(base + prod_url)
            sheets_url.append(str(base + prod_url))
            url_p = driver.page_source
            soup = BeautifulSoup(url_p, "html5lib")


            # Debug Console
            '''
            product_name_value = product_name(soup)
            offer_value = offer(soup)
            price_list_value = price_list(soup)
            availability_ratio = availability(soup)
            product_code_value = product_code_v1(soup)
            # Print v1
            print("-----------------------------------------")
            print("Product Name       : " + str(product_name_value))
            print("Offer              : " + str(offer_value))
            print("Product Price      : " + str(price_list_value[0]))
            print("Sale Price         : " + str(price_list_value[1]))
            print("Availability       : " + '%' + str(availability_ratio))
            print("Product Code       : " + str(product_code_value))
            print("-----------------------------------------")
            print("\n")
            '''

            # Use scraper functions and append to returning data.
            prod_name_list.append(product_name(soup))
            prod_offer_list.append(offer(soup))

            price_list_value = price_list(soup)
            prod_price_list.append(price_list_value[0])
            sale_price_list.append(price_list_value[1])

            availability_list.append(availability(soup))
            prod_code_list.append(product_code_v1(soup))


            # Buffer value for demo purposes.
            # If we set 50, it will just scrape to first 50 product urls.
            i += 1
            print(i)
            if i == 5:
                break


    # Create Pandas Dataframe from gathered datasets.
    data = {
        'URL_List': sheets_url,
        'Product_Name': prod_name_list,
        'Offer': prod_offer_list,
        'Product_Price': prod_price_list,
        'Sale_Price': sale_price_list,
        'Availability': availability_list,
        'Product_Code': prod_code_list
    }
    df_final = pd.DataFrame (data, columns = ['URL_List', 
                                            'Product_Name', 
                                            'Offer', 
                                            'Product_Price', 
                                            'Sale_Price',
                                            'Availability',
                                            'Product_Code'])
    

    # For append these dataframe to google sheets, we use these 2 code blocks.
    data_list = df_final.values.tolist()
    worksheet.append_rows(data_list)






