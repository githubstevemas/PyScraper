import requests
import csv
import os
import re
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


def menu():
    """ ask user for images scrap of not """

    while True:
        menu_choice = input("Want to get images ? y/n ")
        if menu_choice == "n":
            scrap_images = False
            break
        elif menu_choice == "y":
            scrap_images = True
            break

    return scrap_images


def get_categories():
    """ from domain url, get a list of categories urls """

    print("Scraping in progress, take a coffee break...")
    categories_urls_list = []
    response = requests.get(URL_DOMAIN)
    categories_soup = BeautifulSoup(response.text, "html.parser")

    # Find and get the url of all categories in "a" tag with "href" attribute
    categories_list = []
    for a in categories_soup.find_all("a"):
        categories_list.append(a["href"])

    for category in categories_list:
        if "category/books/" in category:
            url_category = "https://books.toscrape.com/" + category

            # Check if there is a page2 on category
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

    book_quantity = 0
    urls_list_length = len(categories_urls_list)
    for i in range(urls_list_length):
        responses = requests.get(categories_urls_list[i])
        soup_book_in_cat = BeautifulSoup(responses.text, "html.parser")

        # Find and get the url of the book in the "h3" tag
        liste_h3 = soup_book_in_cat.find_all("h3")
        for h3 in liste_h3:
            book_quantity += 1
            a_h3 = h3.find("a")
            book_url = "https://books.toscrape.com/catalogue" + a_h3.get("href").replace("../../..", "")

            response = requests.get(book_url)
            soup_book = BeautifulSoup(response.text, "html.parser")

            get_infos(scrap_images, book_url, soup_book)

    print(f"Successfully scraped {book_quantity} books!")


def get_infos(scrap_images, book_url, soup_book):
    """ from soup of all the categories pages get infos for one book """

    data_book_dictionary = {}
    trs_in_soup = soup_book.find_all("tr")
    trs_in_soup_lenght = len(trs_in_soup)

    for j in range(trs_in_soup_lenght):
        cell1 = trs_in_soup[j].find("th").text
        cell2 = trs_in_soup[j].find("td").text
        data_book_dictionary[cell1] = cell2

    # UPC
    upc = data_book_dictionary["UPC"]

    # PRICE WT TAX
    tax_price = data_book_dictionary["Price (incl. tax)"].replace("Â£", "")

    # PRICE WITHOUT TAX
    price = data_book_dictionary["Price (excl. tax)"].replace("Â£", "")

    # COUNT
    count_text = data_book_dictionary["Availability"]
    count = ""
    # extract int from "In stock (XX available)" text
    for k in count_text:
        if k.isdigit():
            count = f"{count}{k}"

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
    li_title = category_ul.find_all("li")
    # Reformat title name to prevent forbidden characters while file writing
    title = re.sub(r'[\\/*?:"<>|]', "", li_title[3].text)

    book_datas = [book_url, upc, title, tax_price, price, count, description, category_name, reviews,
                  url_image]

    create_csv(scrap_images, book_datas)

    return book_datas


def create_csv(scrap_images, book_datas):
    """ create csv output file with date & hour """

    today_date = datetime.now().strftime("%d_%m_%Y")
    # Check if directory already exists
    category_path = f"{SAVE_PATH}/extracted_data_{today_date}/{book_datas[7]}"
    if not os.path.exists(category_path):
        os.makedirs(category_path)

        # Create csv output file with headers
        with open(os.path.join(category_path, "Output.csv"), "w", newline="") as output:
            write = csv.writer(output)
            write.writerow(CSV_HEADER)

    # Add book line to the csv output file
    with open(os.path.join(category_path, "Output.csv"), "a", newline="", encoding="utf-8") as output:
        write = csv.writer(output)
        write.writerow(book_datas)

    # If user wants to save images
    if scrap_images:
        response = requests.get(book_datas[-1])
        if not os.path.exists(os.path.join(SAVE_PATH, "books_images", f"{book_datas[7]}")):
            os.makedirs(os.path.join(SAVE_PATH, "books_images", f"{book_datas[7]}"))

        # Limit characters numbers for file name
        if len(book_datas[2]) > 35:
            book_datas[2] = book_datas[2][:35]

        with open(os.path.join(SAVE_PATH, "books_images", f"{book_datas[7]}", f"{book_datas[2]}.jpg"), "wb") as image:
            image.write(response.content)


scrap_images = menu()
categories_urls_list = get_categories()
get_soup(scrap_images, categories_urls_list)