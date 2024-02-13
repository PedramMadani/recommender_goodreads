# Imports and setup
import re
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics.pairwise import cosine_similarity
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import numpy as np
import time
import os

# Preprocess Text


def preprocess_text(text):
    text = text.lower()
    text = re.sub("(\\d|\\W)+", " ", text)
    return text

# Web Scraping with Selenium


class GoodreadsScraper:
    def __init__(self, webdriver_path):
        self.driver = webdriver.Chrome()

    def search_book(self, book_title):
        self.driver.get("https://www.goodreads.com")
        search_box = self.driver.find_element(By.NAME, "query")
        search_box.send_keys(book_title)
        search_box.send_keys(Keys.RETURN)
        time.sleep(5)  # Dynamic wait could be more efficient here

    def close_popup(self):
        try:
            self.driver.execute_script(
                "document.querySelector('div.modal__close button').click();")
            print("Pop-up closed via JavaScript.")
        except Exception as e:
            print("Error closing pop-up with JavaScript:", e)

    def get_book_details(self):
        first_result = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".bookTitle")))
        first_result.click()
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "div[data-testid='description']")))
        avg_rating = self.driver.find_element(
            By.CSS_SELECTOR, "div.RatingStatistics__rating").text
        summary = self.driver.find_element(
            By.CSS_SELECTOR, "div[data-testid='description']").text
        self.driver.quit()
        return float(avg_rating), preprocess_text(summary)

# Recommendation System


class RecommendationSystem:
    def __init__(self, data, tfidf_vectorizer, scaler):
        self.data = data
        self.tfidf_vectorizer = tfidf_vectorizer
        self.scaler = scaler

    def vectorize_summary(self, summary):
        return self.tfidf_vectorizer.transform([summary])

    def get_recommendations(self, book_title):
        scraper = GoodreadsScraper(
            webdriver_path=os.getenv('CHROME_DRIVER_PATH'))
        scraper.search_book(book_title)
        scraper.close_popup()
        avg_rating, summary = scraper.get_book_details()
        vectorized_summary = self.vectorize_summary(summary)
        cosine_sim = cosine_similarity(
            vectorized_summary, tfidf_matrix).flatten()
        normalized_rating = self.scaler.transform([[avg_rating]])[0][0]
        adjusted_scores = cosine_sim * 0.8 + normalized_rating * 0.2
        top_indices = adjusted_scores.argsort()[-5:][::-1]
        return self.data.iloc[top_indices]['title'].tolist()


# Main execution
if __name__ == "__main__":
    book_title = input("Enter the book title you're interested in: ")
    if book_title:
        data = pd.read_csv('goodreads_books.csv')
        data.drop_duplicates(subset=['title', 'author'], inplace=True)
        data['processed_summary'] = data['summary'].apply(preprocess_text)
        tfidf_vectorizer = TfidfVectorizer()
        tfidf_matrix = tfidf_vectorizer.fit_transform(
            data['processed_summary'])
        scaler = MinMaxScaler()
        data['normalized_ratings'] = scaler.fit_transform(
            data[['average_rate']])
        recommender = RecommendationSystem(data, tfidf_vectorizer, scaler)
        recommended_books = recommender.get_recommendations(book_title)
        print("Recommended Books based on your interest in \"{}\":\n".format(book_title))
        for book in recommended_books:
            print(book)
    else:
        print("No book title provided.")
