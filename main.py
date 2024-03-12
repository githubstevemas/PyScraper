import requests
import csv
import os
import re
from bs4 import BeautifulSoup
from datetime import datetime

# Constants
URL_DOMAIN = "https://books.toscrape.com"
CSV_HEADER = ["product_page_url", "universal_ product_code (upc)", "title", "price_including_tax",
              "price_excluding_tax", "number_available", "product_description", "category", "review_rating",
              "image_url"]
SAVE_PATH = "Outputs"
TODAY_DATE = datetime.now().strftime("%d_%m_%Y")


def get_categories():
    """ from domain url, get a list of categories urls """

    print("Scraping in progress...")
    books_count = 0
    response = requests.get(URL_DOMAIN)
    categories_soup = BeautifulSoup(response.text, "html.parser")

    # Find and get the url of all categories in "a" tag with "href" attribute
    categories_list = []
    for a in categories_soup.find_all("a"):
        categories_list.append(a["href"])

    for category in categories_list:

        if "category/books/" in category:
            urls_category_list = []
            category_books_datas = []
            next_page_number = 2
            url_category = "https://books.toscrape.com/" + category
            urls_category_list.append(url_category)

            get_soup_for_category(books_count, url_category, next_page_number, urls_category_list, category_books_datas)
            create_csv(category_books_datas)

    print(f"Succefully scraped {books_count} books from {URL_DOMAIN}.")


def get_soup_for_category(books_count, url_to_scrap, next_page_number, urls_category_list, category_books_datas):
    """ from categories urls list get soup of all the categories pages """

    responses = requests.get(url_to_scrap)
    cat_soup = BeautifulSoup(responses.text, "html.parser")

    # Check if there is a next page in the curent page
    next_link = cat_soup.find("li", class_="next")

    if next_link:
        next_url = url_to_scrap.rsplit("/", 1)[0] + f"page-{next_page_number}.html"
        next_page_number += 1
        urls_category_list.append(next_url)
        get_soup_for_category(books_count, next_url, next_page_number, urls_category_list, category_books_datas)

    # Get all the books urls from the categories pages
    for i in range(len(urls_category_list)):
        liste_h3 = cat_soup.find_all("h3")

        for h3 in liste_h3:
            books_count += 1
            a_h3 = h3.find("a")
            book_url = "https://books.toscrape.com/catalogue" + a_h3.get("href").replace("../../..", "")

            response = requests.get(book_url)
            soup_book = BeautifulSoup(response.text, "html.parser")

            get_infos(book_url, soup_book, category_books_datas)

    return books_count, category_books_datas


def get_infos(book_url, soup_book, category_books_datas):
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
    # Use regex to prevent forbidden characters while file writing
    title = re.sub(r'[\\/*?:"<>|]', "", li_title)

    book_datas = [book_url, upc, title, tax_price, price, count, description, category_name, reviews,
                  url_image]

    # Scrap images if needed
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

    category_path = f"{SAVE_PATH}/extracted_data_{TODAY_DATE}"

    # Check if directory already exists before writing
    if not os.path.exists(category_path):
        os.makedirs(category_path)

    # Write the category file with headers, then write all infos rows by rows
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
