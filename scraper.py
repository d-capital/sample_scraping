from time import sleep
import json
import requests
#from selenium.webdriver import Chrome
#from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import pandas as pd
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from transliterate import translit
from seleniumwire import webdriver
from seleniumwire.utils import decode

options = {
    'disable_encoding': True
}

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), seleniumwire_options=options)

driver.get('https://wildberries.ru')

#wait until loader goes away
loader = driver.find_element(By.CLASS_NAME, "general-preloader")
WebDriverWait(driver, 15).until(EC.invisibility_of_element_located(loader))
sleep(20)
search = driver.find_element(By.ID,"searchInput")
search.send_keys('елка')
searchBtn = driver.find_element(By.ID,"applySearchBtn")
element = WebDriverWait(driver, 10).until(EC.element_to_be_clickable(searchBtn))
searchBtn.click()


loader = driver.find_element(By.CLASS_NAME, "general-preloader")
WebDriverWait(driver, 15).until(EC.invisibility_of_element_located(loader))
sleep(40)
search_results = driver.find_element(By.CLASS_NAME, "searching-results")

product_cards = driver.find_elements(By.CLASS_NAME, "product-card__wrapper")
ct_data = pd.DataFrame(columns=['name', 'price', 'rating', 'id','country_of_origin'])
ruble_sign = '₽'
countries_dict = {"Kitaj":"China", "Belarus'":"Belarus", "Rossija":"Russia", "Pol'sha":"Poland"} 
product_page_link_template = "https://www.wildberries.ru/catalog/"
for each in product_cards:
    id = each.find_element(By.XPATH, "a[@class='product-card__main j-card-link']").get_attribute("href").split('/')[4]
    print(id)
    name = each.find_element(By.CLASS_NAME, "goods-name").text
    name = translit(name,"ru", reversed=True)
    price = each.find_element(By.CLASS_NAME, "price__lower-price").text
    price = price.replace(ruble_sign, "")
    price = price.replace(" ","")
    rating = each.find_element(By.CLASS_NAME, "product-card__rating").get_attribute("class").split(" ")[2].replace("star","")
    new_row = pd.Series({'name': name, 'price': price, 'rating': rating, 'id': id, 'country_of_origin': None})
    ct_data = pd.concat([ct_data, new_row.to_frame().T], ignore_index=True)

for each in range(len(ct_data)):
    product_id = ct_data.iloc[each]['id']
    product_page_link = product_page_link_template + ct_data.iloc[each]['id'] + "/detail.aspx?targetUrl=XS"
    print("starting data processing for {id}".format(id=ct_data.iloc[each]['id']))
    try: 
        driver.get(product_page_link)
        card_info = '{id}/info/ru/card.json'.format(id = ct_data.iloc[each]['id'])
        try:
            request = driver.wait_for_request(card_info, timeout=30)
            decoded_response = request.response.body.decode('utf-8')
            json_response = json.loads(decoded_response)
            contry_of_origin = [x['value'] for x in json_response['options'] if x['name'] == 'Страна производства'][0]
            contry_of_origin = translit(contry_of_origin,"ru", reversed=True)
            contry_of_origin = countries_dict[contry_of_origin]
            ct_data.iloc[each]['country_of_origin'] = contry_of_origin
            print("got data for product # {id}".format(id = ct_data.iloc[each]['id']))
        except:
            print ("no call for product # {id}".format(id = ct_data.iloc[each]['id']))
    except:
        print("product # {id} failed to load".format(id = product_id))
ct_data.to_csv("christmastrees.csv")