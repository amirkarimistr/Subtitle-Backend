import logging
import os
import zipfile

import bs4
import requests


logger = logging.getLogger("subscene.py")
SUB_QUERY = "https://subscene.com/subtitles/searchbytitle"
SUBSCENE_URL = 'https://subscene.com'
LANGUAGE = {
    "AR": "Arabic",
    "BU": "Burmese",
    "DA": "Danish",
    "DU": "Dutch",
    "EN": "English",
    "FA": "farsi_persian",
    "IN": "Indonesian",
    "IT": "Italian",
    "MA": "Malay",
    "SP": "Spanish",
    "VI": "Vietnamese",
}
MODE = "prompt"
DEFAULT_LANG = LANGUAGE["EN"]  # Default language in which subtitles
# are downloaded.


https_proxy = "https://182.52.90.43:33326"

proxyDict = {"http" : https_proxy}


def scrape_page(url, parameter=""):

    """
    Retrieve content from a url.
    """

    HEADERS = {
        "User-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36"
    }
    if parameter:
        req = requests.get(url, params={"query": parameter}, headers=HEADERS, proxies= proxyDict)
    else:
        req = requests.get(url, headers=HEADERS, proxies= proxyDict)
    if req.status_code != 200:
        logger.debug("{} not retrieved.".format(req.url))
        return
    req_html = bs4.BeautifulSoup(req.content, "lxml")
    return req_html


def zip_extractor(name):
    """
    Extracts zip file obtained from the Subscene site (which contains subtitles).
    """
    try:
        with zipfile.ZipFile(name, "r") as z:
            # srt += [i for i in ZipFile.namelist() if i.endswith('.srt')][0]
            z.extractall(".")
        os.remove(name)
    except Exception as e:
        logger.warning("Zip Extractor Error: {}".format(e))


def silent_mode(title_name, category, name=""):
    """
    An automatic mode for selecting media title from subscene site.
    :param title_name: title names obtained from get_title function.
    """

    def html_navigator(sort_by="Popular"):
        """
     Navigates html tree and select title from it. This function is
     called twice. For example, the default (Popular) category for
     searching in is Popular. It will search title first in popular
     category and then in other categories. If default category
     changes, this process is reversed.
     :param category: selects which category should be searched first in
     the html tree.
     """
        if (
            sort_by == "Popular"
        ):  # Searches in Popular Category and the categories next to it.
            section = category.find_all_next("div", {"class": "title"})
        else:  # Searches in categories above popular tag.
            section = title_name.find_all("div", {"class": "title"})
        for results in section:
            match = 1
            for letter in name.split():
                if letter.lower() in results.a.text.lower():
                    #  print "NAME: %s, RESULT: %s, MATCH: %s" % (letter, results.a.text, match)
                    # Loops through the name (list) and if all the elements of the
                    # list are present in result, returns the link.
                    if match == len(name.split()):
                        return (
                            "https://subscene.com"
                            + results.a.get("href")
                            + "/"
                            + DEFAULT_LANG
                        )
                    match += 1

    # Searches first in Popular category, if found, returns the title name
    obt_link = html_navigator(sort_by="Popular")
    if (
        not obt_link
    ):  # If not found in the popular category, searches in other category
        return html_navigator(sort_by="other_than_popular")
    return obt_link


def cli_mode(titles_name, category):
    """
    A manual mode driven by user, allows user to select subtitles manually
    from the command-line.
    :param titles_name: title names obtained from get_title function.
    """
    media_titles = []  # Contains key names of titles_and_links dictionary.

    for i, x in enumerate(category.find_all_next("div", {"class": "title"})):
        title = x.text.encode("ascii", "ignore").decode("utf-8").strip()
        url = x.a.get('href')
        media_titles.append({'title': title, 'url': SUBSCENE_URL+url})

    return media_titles


def sel_title(name):
    """
    Select title of the media (i.e., Movie, TV-Series)
    :param title_lst: Title Names from the function get_title
    :param name: Media Name. For Example: "Doctor Strange"
    :param mode: Select CLI Mode or Silent Mode.
    URL EXAMPLE:
    https://subscene.com/subtitles/title?query=Doctor.Strange
    """
    logger.info("Selecting title for name: {}".format(name))
    if not name:
        print("Invalid Input.")
        return

    soup = scrape_page(url=SUB_QUERY, parameter=name)
    logger.info("Searching in query: {}".format(SUB_QUERY + "/?query=" + name))
    try:
        if not soup.find("div", {"class": "byTitle"}):
            # URL EXAMPLE (RETURNED):
            # https://subscene.com/subtitles/searchbytitle?query=pele.birth.of.the.legend
            logger.info(
                "Searching in release query: {}".format(
                    SUB_QUERY + "?query=" + name.replace(" ", ".")
                )
            )
            return SUB_QUERY + "?query=" + name.replace(" ", ".")

        elif soup.find("div", {"class": "byTitle"}):
            # for example, if 'abcedesgg' is search-string
            if (
                soup.find("div", {"class": "search-result"}).h2.string
                == "No results found"
            ):

                return -1

    except Exception as e:
        logger.debug("Returning - {}".format(e))
        return

    title_lst = soup.findAll(
        "div", {"class": "search-result"}
    )  # Creates a list of titles
    for titles in title_lst:
        popular = titles.find(
            "h2", {"class": "popular"}
        )  # Searches for the popular tag
        if MODE == "prompt":
            logger.info("Running in PROMPT mode.")
            return cli_mode(titles, category=popular)
        else:
            logger.info("Running in SILENT mode.")
            return silent_mode(
                titles, category=popular, name=name.replace(".", " ")
            )


# Select Subtitles
def sel_sub(page, sub_count=30, name=""):
    """
    Select subtitles from the movie page.
    :param sub_count: Number of subtitles to be downloaded.
    URL EXAMPLE:
    https://subscene.com/subtitles/searchbytitle?query=pele.birth.of.the.legend
    """
    # start_time = time.time()
    soup = scrape_page(page)
    sub_list = []
    current_sub = 0
    for tr in soup.find_all("tr"):
        for link in tr.find_all("td", {"class": "a1"}):
            link = link.find("a")
            if (
                    current_sub < sub_count
                    and "trailer" not in link.text.lower()
                    and link.get("href") not in sub_list
                    and DEFAULT_LANG.lower() in link.get("href")
            ):
                subtitles_dic = {}
                # Link
                for link in tr.find_all("td", {"class": "a1"}):
                    url = link.find("a").get('href')
                    subtitles_dic['url'] = 'https://subscene.com' + url

                    language = link.find('span').text.strip()
                    subtitles_dic['language'] = language

                    title = link.find('span').find_next('span').text.strip()
                    subtitles_dic['title'] = title
                # Author
                for author in tr.find_all("td", {"class": "a5"}):
                    name = author.find('a').text.strip()
                    url = author.find('a').get('href')

                    subtitles_dic['author'] = {
                        'name': name,
                        'url': url
                    }
                # Comment
                for comment in tr.find_all("td", {"class": "a6"}):
                    comment = comment.find('div').text.strip()
                    subtitles_dic['comment'] = comment

                    sub_list.append(subtitles_dic)

                    current_sub += 1

    detail_dic = {}
    # IMDB
    imdb = soup.find('a', {"class": "imdb"}).get('href')
    detail_dic['imdb'] = imdb
    # Title
    title = soup.find('div', {"class": "header"}).find('h2')
    for child_in_title in title.find_all('a'):
        child_in_title.decompose()

    detail_dic['title'] = (title.get_text(strip=True).strip())
    # Poster
    poster = soup.find('div', {"class": "poster"}).find('img').get('src')
    detail_dic['poster'] = poster
    # Year
    year = soup.find('div', {"class": "header"}).find('li')
    for child_in_year in year.findAll('strong'):
        child_in_year.decompose()
    detail_dic['year'] = (year.get_text(strip=True).strip())
    detail_dic['subtitles'] = sub_list

    return detail_dic


def dl_sub(page):
    """
    Download subtitles obtained from the select_subtitle
    function i.e., movie subtitles links.
    """
    # start_time = time.time()
    soup = scrape_page(page)
    div = soup.find("div", {"class": "download"})
    down_link = "https://subf2m.co" + div.find("a").get("href")
    download_dic = {
        'title': '',
        'poster': '',
        'author': '',
        'comment': '',
        'preview': '',
        'info': '',
        'details': '',
        'download_url': down_link
    }
    return download_dic


def new_sub():
    soup = scrape_page(SUBSCENE_URL)

    popular_list = []
    popular_tv_list = []
    recent_list = []

    url_list = []
    poster_list = []
    title_list = []

    # Popular Subtitle
    popular_subtitles = soup.select('div.box')[0]
    for ul in popular_subtitles.select('ul.details'):
        # Get Title
        for div_title in ul.select('div.title'):
            title = div_title.select_one('a').text.strip()
            title_list.append(title)

        # Get Poster
        for div_poster in ul.select('div.poster'):
            poster = div_poster.select_one('img')['src']
            poster_list.append(poster)

        # Get URL
        for movie_url in ul.select('li'):
            for child_url in movie_url.select('li'):
                child_url.decompose()
            try:
                url = 'https://subscene.com' + movie_url.select_one('a')['href']
                url_list.append(url)
            except:
                ''''
                Just do nothing 
                '''
    for i in range(0, len(title_list)):
        popular_item = {
            'title': title_list[i],
            'poster': poster_list[i],
            'poseter': poster_list[i],
            'url': url_list[i]
        }
        popular_list.append(popular_item)

    # Popular TV Subtitle
    popular_tv_shows = soup.select('div.box')[1]
    for ul in popular_tv_shows.select('ul.details'):
        popular_tv_item = {}
        # Get Title
        for div_title in ul.select('div.title'):
            title = div_title.select_one('a').text.strip()
            popular_tv_item['title'] = title
        # Get Poster
        for div_poster in ul.select('div.poster'):
            poster = div_poster.select_one('img')['src']
            popular_tv_item['poster'] = poster
            popular_tv_item['poseter'] = poster
        # Get URL
        for movie_url in ul.select('li'):
            for child_url in movie_url.select('li'):
                child_url.decompose()
            try:
                url = 'https://subscene.com' + movie_url.select_one('a')['href']
                popular_tv_item['url'] = url.strip()
            except:
                ''''
                Just do nothing 
                '''
        popular_tv_list.append(popular_tv_item)

    div_content = soup.select_one('div.content')
    for recent_li in div_content.select('li'):
        recent_item = {}
        # Get URL
        div_name = recent_li.select_one('div.name')
        url = "https://subscene.com/subtitles" + div_name.select_one('a')['href']
        recent_item['url'] = url

        # Get Title
        title = div_name.select_one('a')
        title_span = title.select_one('span').decompose()
        recent_item['title'] = title.text.strip()

        # Get Contributor
        contributor = recent_li.select_one('address')
        name = contributor.select_one('a').text.strip()
        url = contributor.select_one('a')['href']
        recent_item['contributor'] = {
            'name': name,
            'url': url
        }

        recent_list.append(recent_item)

    new_film_dic = {
        'popular': popular_list,
        'popular_tv': popular_tv_list,
        'recent': recent_list
    }
    return new_film_dic




