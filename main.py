import requests
import csv
import os
import re
from bs4 import BeautifulSoup
from datetime import datetime

URL_DOMAIN = "https://books.toscrape.com"
CSV_HEADER = ["product_page_url", "universal_ product_code (upc)", "title", "price_including_tax",
              "price_excluding_tax", "number_available", "product_description", "category", "review_rating",
              "image_url"]
SAVE_PATH = "Outputs"
TODAY_DATE = datetime.now().strftime("%d_%m_%Y")


def get_categories():
    """ from domain url, get a list of categories urls """

    print("Scraping in progress...")
    response = requests.get(URL_DOMAIN)
    categories_soup = BeautifulSoup(response.text, "html.parser")

    categories_list = []
    for a in categories_soup.find_all("a"):
        categories_list.append(a["href"])

    for category in categories_list:

        if "category/books/" in category:
            urls_category_list = []

            url_category = "https://books.toscrape.com/" + category
            urls_category_list.append(url_category)

            category_books_datas = get_categories_soups(url_category)
            create_csv(category_books_datas)

    print(f" {URL_DOMAIN} succefully scraped.")


def get_categories_soups(url_category):
    next_page_number = 1
    categories_soups = []

    while True:
        try:
            responses = requests.get(url_category)
            cat_soup = BeautifulSoup(responses.text, "html.parser")
            categories_soups.append(cat_soup)

            next_page_number += 1
            next_link = cat_soup.find("li", class_="next")
            next_url = next_link.rsplit("/", 1)[0] + f"page-{next_page_number}.html"

            url_category = next_url
        except:
            break

    category_books_datas = get_books_category(categories_soups)
    return category_books_datas


def get_books_category(categories_soups):
    """ from category url get books of all the category pages """

    category_books_datas = []
    for i in range(len(categories_soups)):
        liste_h3 = categories_soups[i].find_all("h3")

        for h3 in liste_h3:
            a_h3 = h3.find("a")
            book_url = "https://books.toscrape.com/catalogue" + a_h3.get("href").replace("../../..", "")

            response = requests.get(book_url)
            soup_book = BeautifulSoup(response.text, "html.parser")

            book_datas = get_infos(book_url, soup_book)
            category_books_datas.append(book_datas)

    return category_books_datas


def get_infos(book_url, soup_book):
    """ from soup of all the categories pages get infos for one book """

    upc = soup_book.find_all("td")[0].text

    tax_price = soup_book.find_all("td")[2].text.replace("Â£", "")

    price = soup_book.find_all("td")[3].text.replace("Â£", "")

    count = re.search(r'\d+', soup_book.find_all("td")[5].text).group()

    p_soup = soup_book.find_all("p")[2]

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

    image = soup_book.find("img")
    url_image = URL_DOMAIN + image["src"].replace("../..", "")

    if soup_book.find("p", class_=""):
        description = soup_book.find("p", class_="").text
    else:
        description = "No description."

    category_ul = soup_book.find("ul", class_="breadcrumb")
    category_name = category_ul.find_all("a")[2].text

    li_title = category_ul.find_all("li")[3].text

    title = re.sub(r'[\\/*?:"<>|]', "", li_title)

    book_datas = [book_url, upc, title, tax_price, price, count, description, category_name, reviews,
                  url_image]

    if scrap_images:
        get_images(book_datas)

    return book_datas


def get_images(book_datas):

    if not os.path.exists(os.path.join(SAVE_PATH, "books_images", f"{book_datas[7]}")):
        os.makedirs(os.path.join(SAVE_PATH, "books_images", f"{book_datas[7]}"))

    response = requests.get(book_datas[-1])

    if len(book_datas[2]) > 35:
        book_datas[2] = book_datas[2][:35]

    with open(os.path.join(SAVE_PATH, "books_images", f"{book_datas[7]}",
                           f"{book_datas[2]}.jpg"), "wb") as image:
        image.write(response.content)


def create_csv(category_books_datas):
    """ create csv output file with date & hour """

    category_path = f"{SAVE_PATH}/extracted_data_{TODAY_DATE}"

    if not os.path.exists(category_path):
        os.makedirs(category_path)

    with open(os.path.join(category_path, f"Output - {category_books_datas[0][7]}.csv"),
              "w", newline="", encoding="utf-8") as output:
        write = csv.writer(output)
        write.writerow(CSV_HEADER)

        for i in range(len(category_books_datas)):
            write.writerow(category_books_datas[i])


while True:
    menu_choice = input("Want to get images ? y/n ")
    if menu_choice == "n":
        scrap_images = False
        break
    elif menu_choice == "y":
        scrap_images = True
        break

get_categories()
