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
SAVE_PATH = f"Outputs/extracted_data_{datetime.now().strftime("%d_%m_%Y")}"


def get_main_categories():
    """ from domain url get a list of categories urls """

    print("Scraping in progress...")
    response = requests.get(URL_DOMAIN)
    main_soup = BeautifulSoup(response.text, "html.parser")

    create_directories(main_soup)

    categories_list = main_soup.find('div', class_='side_categories').find('ul').find_all('a')

    for category in categories_list:
        if "category/books/" in category["href"]:
            url_category = "https://books.toscrape.com/" + category["href"]

            category_books_datas = get_soup_category(url_category)
            create_csv(category_books_datas)

    print(f"{URL_DOMAIN} succefully scraped.")


def get_soup_category(url_category):
    """ from category url get his soup and check if next page is present """

    next_page_number = 1
    category_page_datas = []

    while url_category:

        response = requests.get(url_category)
        category_soup = BeautifulSoup(response.text, "html.parser")

        category_books_datas = get_books(category_soup, category_page_datas)

        next_page_number += 1
        if category_soup.find("li", class_="next"):
            url_category = url_category.rsplit("/", 1)[0] + f"/page-{next_page_number}.html"
        else:
            break

    return category_books_datas


def get_books(category_soup, category_page_datas):
    """ from category url get all books of the page """

    h3_list = category_soup.find_all("h3")

    for h3 in h3_list:

        book_url = "https://books.toscrape.com/catalogue" + h3.find("a")["href"].replace("../../..", "")

        response = requests.get(book_url)
        soup_book = BeautifulSoup(response.text, "html.parser")

        book_datas = get_book_infos(book_url, soup_book)
        category_page_datas.append(book_datas)

    return category_page_datas


def get_book_infos(book_url, soup_book):
    """ from soup of all the categories pages get infos for one book """

    upc = soup_book.find_all("td")[0].text

    tax_price = soup_book.find_all("td")[2].text.replace("Â£", "")

    price = soup_book.find_all("td")[3].text.replace("Â£", "")

    count = re.search(r'\d+', soup_book.find_all("td")[5].text).group()

    p_soup = soup_book.find_all("p")[2]
    if p_soup["class"][1] == "One":
        review_rating = 1
    elif p_soup["class"][1] == "Two":
        review_rating = 2
    elif p_soup["class"][1] == "Three":
        review_rating = 3
    elif p_soup["class"][1] == "Four":
        review_rating = 4
    else:
        review_rating = 5

    url_image = URL_DOMAIN + soup_book.find("img")["src"].replace("../..", "")

    if soup_book.find("p", class_=""):
        description = soup_book.find("p", class_="").text
    else:
        description = "No description."

    category_ul = soup_book.find("ul", class_="breadcrumb")
    category_name = category_ul.find_all("a")[2].text

    li_title = category_ul.find_all("li")[3].text
    title = re.sub(r'[\\/*?:"<>|]', "", li_title)

    book_datas = [book_url, upc, title, tax_price, price, count, description, category_name, review_rating,
                  url_image]

    if scrap_images:
        get_images(book_datas)

    return book_datas


def create_directories(main_soup):
    """ from main page create directories for images and csv outputs """

    if not os.path.exists(SAVE_PATH):
        os.makedirs(SAVE_PATH)

    if scrap_images:
        categories = main_soup.find("ul", class_="nav nav-list")

        for i in categories.find_all("li"):
            category_name = i.find("a").text.strip()
            os.makedirs(os.path.join("Outputs", "books_images", f"{category_name}"))


def get_images(book_datas):
    """ from url image book write image on local path """

    response = requests.get(book_datas[-1])

    if len(book_datas[2]) > 35:
        book_datas[2] = book_datas[2][:35]

    with open(os.path.join("Outputs", "books_images", f"{book_datas[7]}",
                           f"{book_datas[2]}.jpg"), "wb") as image:
        image.write(response.content)


def create_csv(category_books_datas):
    """ create csv output file """

    with open(os.path.join(SAVE_PATH, f"Output - {category_books_datas[0][7]}.csv"),
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

get_main_categories()
