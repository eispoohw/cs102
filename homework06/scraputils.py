""" Collecting a data (latest news) from 'Hacker News' as a list of dictionaries """

import typing as tp

import requests
from bs4 import BeautifulSoup

URL = "https://news.ycombinator.com/"


def extract_news(parser: BeautifulSoup) -> tp.List[tp.Dict[str, tp.Union[str, int]]]:
    """ Extract news from a given web page """

    news_list = []
    rows = parser.table.find("table", {"class": "itemlist"}).findAll("tr")
    keys = ["author", "comments", "points", "title", "url"]
    temp_news = dict.fromkeys(keys)

    for item in rows:
        current_case = item.get("class")
        if current_case is None:
            points = item.find("span", {"class": "score"})
            if points is None:
                temp_news["points"] = 0
            else:
                temp_news["points"] = int(points.text.split()[0])

            author = item.find("a", {"class": "hnuser"})
            if author is not None:
                temp_news["author"] = author.text

            comments = item.findAll("a")[-1].text
            idx = comments.find("\xa0comments")
            if idx == -1:
                temp_news["comments"] = 0
            else:
                temp_news["comments"] = int(comments[:idx])

        elif current_case[0] == "athing":
            athing = item.find("a", {"class": "storylink"})
            temp_news["title"] = athing.text
            temp_news["url"] = athing["href"]

        elif current_case[0] == "spacer":
            news_list.append(temp_news)
            temp_news = dict.fromkeys(keys)

    return news_list


def extract_next_page(parser: BeautifulSoup) -> str:
    """ Extract next page URL """
    return str(parser.find("a", {"class": "morelink"})["href"])


def get_news(url: str, n_pages: int = 1) -> tp.List[tp.Dict[str, tp.Union[int, str]]]:
    """ Collect news from a given web page """
    news = []
    while n_pages:
        print("Collecting data from page: {}".format(url))
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        news_list = extract_news(soup)
        next_page = extract_next_page(soup)
        url = "https://news.ycombinator.com/" + next_page
        news.extend(news_list)
        n_pages -= 1
    return news


if __name__ == "__main__":
    news_test = get_news(url="https://news.ycombinator.com/", n_pages=10)
    print(
        "Collected ",
        len(news_test),
        " news\n10th item: ",
        news_test[9],
        "\nLast item: ",
        news_test[len(news_test) - 1],
    )
