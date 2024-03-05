# PyScraper :snake:

Get all the datas from [books.toscrape.com](https://books.toscrape.com).

The script uses the BeautifulSoup library to parse the HTML content of the website and extract information such as book titles, prices, ratings, and descriptions.


## How it works

When launched, you can choose if you want to download the corresponding image files of books. The informations (title, price, description, etc..) will be saved locally in an "Outputs" folder, and each category of books will be saved in separate CSV files. Finally, the date of the scraping will be included in the name of the folder for a better manage of backups.

## Requirements

- Python 3.x

## How to run

Once the code has been downloaded, go to the project directory and enter the following commands in terminal :

  `python -m venv env` *install a new vitual environement*
    
  `env/Scripts/activate` *activate the environement*
    
  `pip install -r requirements.txt` *install all the depedencies*
    
  `python main.py` *run the code*

  `deactivate` *when over, deactivate the environement*
  

> [!NOTE]
> The commands above are for Windows use. Go to the official [Python documentation](https://docs.python.org/3/tutorial/venv.html) for MacOS or Unix usage.

## Contact
Feel free to [mail me](mailto:mas.ste@gmail.com) for any questions, comments, or suggestions.

