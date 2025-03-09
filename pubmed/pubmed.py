import requests
import logging
from deep_translator import GoogleTranslator
import re
import bs4
import os
import pandas as pd
import json



logger = logging.getLogger(__name__)


class Fetch:
    def __init__(self, query="", force_article=False, count=None):
        self.query = query
        self._query_change = True
        self.limit_article = count
        self._ids = {"value": [], "parsed": False}
        self._metadata = {"value": [], "parsed": False}
        self.force_article = force_article

    def __extract_email(self, affil):
        logger.debug(f"Extracting Email .....")
        email_pattern = r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b'
        emails = re.findall(email_pattern, affil)
        if emails:
            logger.debug(f"Email Found")
            affil = re.sub(email_pattern, '', affil)
        else:
            logger.debug(f"Email not present in affiliation string")
        return emails, affil

    def __translate_sentence(self, sentence):
        try:
            translated_affiliation = GoogleTranslator(
                source='auto', target='en').translate(sentence)
            return translated_affiliation
        except Exception as e:
            logger.debug(f"Problume in translating")
            return sentence

        # url = "https://deep-translator-api.azurewebsites.net/google/"
        # data = {"source": "auto", "target": "en", "text": f"{sentence}"}
        # response = requests.post(url, json=data)
        # if response.status_code == 200:
        #     try:
        #         respo = response.json()
        #         if not respo["error"]:
        #             logger.debug(f"-- Translated --")
        #             return respo["translation"]
        #     except:
        #         pass
        # logger.debug(f"Problume in translating")
        # return sentence

    def __find_affil(self, affiliation):
        logger.debug(f"Checking if Non-affiliate or affiliate .....")
        academic_keywords = ["university", "institute", "college", "faculty",
                             "school", "research center", "department of", "national lab", "academic"]
        logger.debug(f"Translating Affiliation if not in english.")
        translated_affiliation = self.__translate_sentence(affiliation).lower()
        for word in academic_keywords:
            if word in translated_affiliation:
                logger.debug(f"Is affiliated in a university or institute.")
                return False
        logger.debug(f"Non Affiliate")
        return translated_affiliation

    def __get_metadata(self, xml):
        logger.info("Starting search for article with metadata")
        respo_list = []
        soup = bs4.BeautifulSoup(xml, "xml")
        articles = soup.find_all("PubmedArticle")
        if not articles:
            logger.info("Article Not Found")
            return respo_list
        else:
            logger.info(f"Found {len(articles)} articles")
        count = 0
        for article in articles:
            count += 1
            logger.debug(f"Parsing Article Number {count}")

            article_dict = {}
            date_set = article.find("PubDate")
            authors = article.find_all("Author")
            article_dict["authors"] = []
            for author in authors:
                author_dict = {}
                f_name = author.find("ForeName")
                affil = author.find("Affiliation")
                if f_name and affil:
                    author_name = f_name.text + \
                        author.find("LastName").text if author.find(
                            "LastName") else f_name.text

                    affiliation = author.find("Affiliation").text
                    logger.debug(
                        "\n-------------------------new author--------------------------\n")
                    logger.debug(
                        f"Author found with affiliation: {author_name} \naffiliation: {affiliation}")

                    email, affiliation = self.__extract_email(affiliation)
                    author_affiliation = self.__find_affil(affiliation)

                    if not author_affiliation:
                        continue

                    author_dict["name"] = author_name
                    author_dict["affiliation"] = author_affiliation
                    author_dict["email"] = email
                    article_dict["authors"].append(author_dict)

            if not self.force_article:
                if not article_dict["authors"]:
                    logger.debug(
                        f"Article does not contain valid authers. Skipping .....")
                    continue
            else:
                logger.debug(
                    f"Force Article is active. Output will contain article without author")
            article_dict["title"] = article.find("ArticleTitle").text
            day = date_set.find("Day")
            month = date_set.find("Month")
            year = date_set.find("Year")
            article_dict["date"] = " - ".join(
                i.text for i in [day, month, year] if i)
            respo_list.append(article_dict)
            if type(self.limit_article) == int:
                if count == self.limit_article:
                    break
        return respo_list

    def __fetch_data(self, search=True):
        params = {}
        params["db"] = "pubmed"
        if search:
            to_get = "ids"
            params["retmode"] = "json"
            params["term"] = self.query
            url_sub_path = "esearch"
            logger.debug("query search param data is added")
        else:
            to_get = "Paper Metadata"
            params["retmode"] = "xml"
            url_sub_path = "efetch"
            params["id"] = ",".join(i for i in self._ids["value"])
            logger.debug("fetch param data is added with ids")

        logger.info(f"Searching for {to_get}")

        url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/{url_sub_path}.fcgi"

        logger.debug(f"Sending request to {url} for {to_get}")
        response = requests.get(url, params=params)

        if response.status_code == 200:
            if search:
                try:
                    data = response.json()
                    metadata = data["esearchresult"]["idlist"]
                    logger.debug(f'Recieved {to_get} as {params["retmode"]}')
                    return metadata
                except:
                    logger.error(
                        f"Error while parsing E-utility {to_get} response JSON")
                    return []
            else:
                return self.__get_metadata(response.content)
        logger.error(
            f"E-utility error 404: Not Found while fetching {to_get} result")
        return []

    def set_query(self, query):
        logger.info("Adding Query......")
        if not self.query == query:
            self.query = query
            self._query_change = True
            logger.debug("Query Added and query_change : True")
        else:
            logger.warning("Query is same as before.")

    def get_ids(self):
        if not self.query:
            logger.warning("Query or Input is empty set using set_query()")
        if self._query_change:
            self._ids["value"] = self.__fetch_data(search=True)
            self._ids["parsed"] = True
            self._query_change = False
        return self._ids["value"]

    def get_metadata(self):
        if not self.query:
            logger.warning("Query or Input is empty set using set_query()")
        if self._query_change or (not self._metadata["parsed"] and not self._ids["parsed"]):
            self._ids["value"] = self.__fetch_data(search=True)
            self._ids["parsed"] = True
            if not self._ids["value"]:
                logger.warning("No ids found Please search again")
            else:
                self._metadata["value"] = self.__fetch_data(search=False)
                self._metadata["parsed"] = True

        elif not self._metadata["parsed"] and self._ids["parsed"]:
            self._metadata["value"] = self.__fetch_data(search=False)
            self._metadata["parsed"] = True

        self._query_change = False
        return self._metadata["value"]

    def __get_df(self, data):
        df = pd.json_normalize(data, 'authors', ['title', 'date'], errors='ignore')
        if df.empty:
            df = pd.DataFrame(data)[['title', 'date']]
        else:
            df['author_index'] = df.groupby(['title']).cumcount() + 1
            df = df.pivot(index=['title', 'date'], columns='author_index', values=['name', 'affiliation', 'email'])
            df.columns = [f"author_{col[1]}_{col[0]}" for col in df.columns]
            df.reset_index(inplace=True)
        return df

    def save(self, filename):
        data = self.get_metadata()
        if not data:
            logger.info(f"Save fail : No data found")
            return
        if not filename:
            print(data)
            return

        base_name = os.path.basename(filename)
        directory = os.path.dirname(filename)
        if not base_name or '.' not in base_name:
            logger.error(
                "Error: The path does not include a file name or it is a folder path.")
        elif directory and not os.path.exists(directory):
            logger.error(f"Error: Path directory does not exist.")
        elif filename.endswith(".xlsx"):
            self.__get_df(data).to_excel(filename, index=False)
            logger.info(f"saved file: location - {filename}")
            return
        elif filename.endswith(".csv"):
            self.__get_df(data).to_csv(filename, index=False)
            logger.info(f"saved file: location - {filename}")
            return
        elif filename.endswith(".json"):
            with open(filename, "w",encoding="utf-8") as f:
                json.dump(self.get_metadata(), f, ensure_ascii=True)
            logger.info(f"saved file: location - {filename}")
            return
        logger.warning('Extension Supported: .json, .csv and .xlsx')
        print(data)
