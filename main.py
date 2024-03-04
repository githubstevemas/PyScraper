import requests
import csv
import os
import re
from bs4 import BeautifulSoup
from datetime import datetime

""" Get all the infos of books (titles, prices, etc) from books.toscrape.com """

""" Things to do/change :
    [ ] global statement errors
    [ ] shadows name from outer scope error
"""

URL_DOMAIN = "https://books.toscrape.com"
CSV_HEADER = ["product_page_url", "universal_ product_code (upc)", "title", "price_including_tax",
              "price_excluding_tax", "number_available", "product_description", "category", "review_rating",
              "image_url"]
SAVE_PATH = "Outputs"


def menu():
    menu_choice = input("Scrape images ? y/n ")
    if menu_choice == "n":
        scrap_images = False
    else:
        scrap_images = True

    return scrap_images


def get_categories(URL_DOMAIN):
    """ from domain url, get a list of categories urls """
    print("Getting datas from website...")
    categories_urls_list = []
    response = requests.get(URL_DOMAIN)
    categories_soup = BeautifulSoup(response.text, "html.parser")

    categories_list = []
    for a in categories_soup.find_all("a"):
        categories_list.append(a["href"])

    for category in categories_list:
        if "category/books/" in category:
            url_category = "https://books.toscrape.com/" + category

            n = 2

            while category:
                next_page_category = url_category.replace("index.html", f"page-{n}.html")
                try:
                    response_nest_page = requests.get(next_page_category)
                    response_nest_page.raise_for_status()
                    categories_urls_list.append(next_page_category)
                    n += 1

                except:
                    break

            categories_urls_list.append(url_category)

    return categories_urls_list


def get_soup(scrap_images, categories_urls_list):
    """ from categories urls list get soup of all the categories pages """

    urls_list_length = len(categories_urls_list)
    for i in range(urls_list_length):
        responses = requests.get(categories_urls_list[i])
        soup_book_in_cat = BeautifulSoup(responses.text, "html.parser")

        liste_h3 = soup_book_in_cat.find_all("h3")

        for h3 in liste_h3:
            a_h3 = h3.find("a")
            book_url = "https://books.toscrape.com/catalogue" + a_h3.get("href").replace("../../..", "")

            response = requests.get(book_url)
            soup_book = BeautifulSoup(response.text, "html.parser")

            get_infos(scrap_images, URL_DOMAIN, book_url, soup_book)

    print("Scrap finished!")


def get_infos(scrap_images, URL_DOMAIN, book_url, soup_book):
    """ from soup of all the categories pages get infos for one book """

    data_book_dictionary = {}
    soup_book_lenght = len(soup_book)

    for i in range(soup_book_lenght):

        trs_in_soups = soup_book.find_all("tr")
        trs_in_soups_lenght = len(trs_in_soups)

        for j in range(trs_in_soups_lenght):
            cell1 = trs_in_soups[j].find("th").text
            cell2 = trs_in_soups[j].find("td").text
            data_book_dictionary[cell1] = cell2

        # UPC
        upc = data_book_dictionary["UPC"]
        # PRICE WT TAX
        english_price_tax = data_book_dictionary["Price (incl. tax)"]
        tax_price = "".join(english_price_tax).replace("Â£", "")
        # PRICE WITHOUT TAX
        english_price = data_book_dictionary["Price (excl. tax)"]
        price = "".join(english_price).replace("Â£", "")
        # COUNT
        count = data_book_dictionary["Availability"]
        # RATING
        reviews = data_book_dictionary["Number of reviews"]
        # IMAGE URL
        image = soup_book.find("img")
        end_url_image = image["src"].replace("../..", "")
        url_image = URL_DOMAIN + end_url_image
        # DESCRIPTION
        if soup_book.find("p", class_=""):
            description = soup_book.find("p", class_="").text
        else:
            description = "No description."
        # CATEGORY
        category_ul = soup_book.find("ul", class_="breadcrumb")
        a_category = category_ul.find_all("a")
        category_name = a_category[2].text
        # TITRE
        li_title = category_ul.find_all("li")
        title = re.sub(r'[\\/*?:"<>|]', "", li_title[3].text)

        book_datas = [book_url, upc, title, tax_price, price, count, description, category_name, reviews,
                      url_image]

    create_csv(scrap_images, book_datas)

    return book_datas


def create_csv(scrap_images, book_datas):
    """ create csv output file with date & hour """

    # create cvs output file with date & hour
    today_date = datetime.now().strftime("%d_%m_%Y")

    # check if directory exists
    category_path = f"{SAVE_PATH}/{today_date}/{book_datas[7]}"

    if not os.path.exists(category_path):
        print(f"Scraping the {book_datas[7]} category...")
        os.makedirs(category_path)

        with open(os.path.join(category_path, "Output.csv"), "w", newline="") as output:
            write = csv.writer(output)
            write.writerow(CSV_HEADER)

    with open(os.path.join(category_path, "Output.csv"), "a", newline="", encoding="utf-8") as output:
        write = csv.writer(output)
        write.writerow(book_datas)

    # SAVE BOOK IMAGE
    if scrap_images:
        response = requests.get(book_datas[-1])
        if not os.path.exists(os.path.join(SAVE_PATH, "images", f"{book_datas[7]}")):
            os.makedirs(os.path.join(SAVE_PATH, "images", f"{book_datas[7]}"))

        if len(book_datas[2]) > 35:
            book_datas[2] = book_datas[2][:35]

        with open(os.path.join(SAVE_PATH, "images", f"{book_datas[7]}", f"{book_datas[2]}.jpg"), "wb") as image:
            image.write(response.content)


scrap_images = menu()
categories_urls_list = get_categories(URL_DOMAIN)
get_soup(scrap_images, categories_urls_list)