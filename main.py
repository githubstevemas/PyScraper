import requests
import csv
import os
import re
import time
from bs4 import BeautifulSoup
from datetime import datetime

""" With BeautifulSoup library, get informations from books.toscrape.com like book titles, prices, ratings, 
descriptions and many more.

Autor : Steve Mas
Date : 03/24 

Improvements ideas :
    - Possibility to choose path save
    - Check last update of website (maybe header check ??)
    - Scrap choosen categories
"""

# Constants
URL_DOMAIN = "https://books.toscrape.com"
CSV_HEADER = ["product_page_url", "universal_ product_code (upc)", "title", "price_including_tax",
              "price_excluding_tax", "number_available", "product_description", "category", "review_rating",
              "image_url"]
SAVE_PATH = "Outputs"
TODAY_DATE = datetime.now().strftime("%d_%m_%Y")


def get_categories():
    """ from domain url, get a list of categories urls """

    print("Scraping in progress, take a coffee break...")
    books_count = 0
    response = requests.get(URL_DOMAIN)
    categories_soup = BeautifulSoup(response.text, "html.parser")

    # Find and get the url of all categories in "a" tag with "href" attribute
    categories_list = []
    for a in categories_soup.find_all("a"):
        categories_list.append(a["href"])

    for category in categories_list:

        if "category/books/" in category:
            categories_urls_list = []
            url_category = "https://books.toscrape.com/" + category

            # Check if there is a page2 on category
            n = 2
            while category:
                next_page_category = url_category.replace("index.html", f"page-{n}.html")
                try:
                    response_next_page = requests.get(next_page_category)
                    response_next_page.raise_for_status()
                    categories_urls_list.append(next_page_category)
                    n += 1
                except:
                    category_books_datas = []
                    break

            categories_urls_list.append(url_category)

            get_soup(books_count, category_books_datas, categories_urls_list)
            create_csv(category_books_datas)
    print(f"Succefully scraped ")


def get_soup(books_count, category_books_datas, categories_urls_list):
    """ from categories urls list get soup of all the categories pages """

    urls_list_length = len(categories_urls_list)
    for i in range(urls_list_length):
        responses = requests.get(categories_urls_list[i])
        soup_book_in_cat = BeautifulSoup(responses.text, "html.parser")

        # Find and get the url of the book in the "h3" tag
        liste_h3 = soup_book_in_cat.find_all("h3")
        for h3 in liste_h3:
            books_count += 1
            a_h3 = h3.find("a")
            book_url = "https://books.toscrape.com/catalogue" + a_h3.get("href").replace("../../..", "")

            response = requests.get(book_url)
            soup_book = BeautifulSoup(response.text, "html.parser")

            get_infos(category_books_datas, book_url, soup_book)

    end_time = time.time()

    print(f"Successfully scraped {books_count} books in {round((end_time - start_time) / 60, 2)} minutes!")


def get_infos(category_books_datas, book_url, soup_book):
    """ from soup of all the categories pages get infos for one book """

    # UPC
    upc = soup_book.find_all("td")[0].text

    # PRICE WT TAX
    tax_price = soup_book.find_all("td")[2].text.replace("Â£", "")

    # PRICE WITHOUT TAX
    price = soup_book.find_all("td")[3].text.replace("Â£", "")

    # COUNT
    count = re.search(r'\d+', soup_book.find_all("td")[5].text).group()

    # REVIEWS RATING
    p_soup = soup_book.find_all("p")[2]
    # Find reviews in "star-rating" class and reformat str to int
    reviews_letters = p_soup["class"][1]
    if reviews_letters == "One":
        reviews = 1
    elif reviews_letters == "Two":
        reviews = 2
    elif reviews_letters == "Three":
        reviews = 3
    elif reviews_letters == "Four":
        reviews = 4
    else:
        reviews = 5

    # IMAGE URL
    image = soup_book.find("img")
    url_image = URL_DOMAIN + image["src"].replace("../..", "")

    # DESCRIPTION
    # Exeption if None
    if soup_book.find("p", class_=""):
        description = soup_book.find("p", class_="").text
    else:
        description = "No description."

    # CATEGORY
    category_ul = soup_book.find("ul", class_="breadcrumb")
    category_name = category_ul.find_all("a")[2].text

    # TITRE
    li_title = category_ul.find_all("li")[3].text
    # Reformat title name to prevent forbidden characters while file writing
    title = re.sub(r'[\\/*?:"<>|]', "", li_title)

    book_datas = [book_url, upc, title, tax_price, price, count, description, category_name, reviews,
                  url_image]

    if scrap_images:

        if not os.path.exists(os.path.join(SAVE_PATH, "books_images", f"{book_datas[7]}")):
            os.makedirs(os.path.join(SAVE_PATH, "books_images", f"{book_datas[7]}"))

        response = requests.get(book_datas[-1])

        if len(book_datas[2]) > 35:
            book_datas[2] = book_datas[2][:35]

        with open(os.path.join(SAVE_PATH, "books_images", f"{book_datas[7]}",
                               f"{book_datas[2]}.jpg"), "wb") as image:
            image.write(response.content)

    category_books_datas.append(book_datas)
    return category_books_datas


def create_csv(category_books_datas):
    """ create csv output file with date & hour """

    category_path = f"{SAVE_PATH}/extracted_data_{TODAY_DATE}/{category_books_datas[0][7]}"

    # Check if directory already exists before writing
    if not os.path.exists(category_path):
        os.makedirs(category_path)

    lenght_category_books = len(category_books_datas)

    with open(os.path.join(category_path, "Output.csv"), "w", newline="", encoding="utf-8") as output:
        write = csv.writer(output)
        write.writerow(CSV_HEADER)

        for i in range(lenght_category_books):
            write.writerow(category_books_datas[i])


while True:
    menu_choice = input("Want to get images ? y/n ")
    if menu_choice == "n":
        scrap_images = False
        break
    elif menu_choice == "y":
        scrap_images = True
        break

start_time = time.time()

get_categories()
