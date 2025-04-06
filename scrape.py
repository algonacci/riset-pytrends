import requests
import xml.etree.ElementTree as ET
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from bs4 import BeautifulSoup
from datetime import datetime
import re
import time
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class GoogleTrendsCompleteData:
    """
    Scraper untuk mendapatkan data Google Trends Indonesia lengkap,
    mengkombinasikan RSS Feed dan scraping web.
    """
    
    def __init__(self, country="ID"):
        """
        Inisialisasi scraper.
        
        Parameters:
        -----------
        country : str
            Kode negara (default: ID untuk Indonesia)
        """
        self.country = country
        self.rss_url = f"https://trends.google.co.id/trending/rss?geo={country}"
        self.web_url = f"https://trends.google.com/trends/trendingsearches/daily?geo={country}"
        self.session = self._create_session()
    
    def _create_session(self):
        """
        Membuat session requests dengan user-agent yang tepat.
        """
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xml,application/xhtml+xml,application/rss+xml"
        })
        return session
    
    def get_rss_trends(self):
        """
        Mengambil trending topics dari feed RSS Google Trends.
        
        Returns:
        --------
        list
            Daftar trending topics dari RSS feed
        """
        try:
            response = self.session.get(self.rss_url)
            response.raise_for_status()
            
            # Parse XML
            root = ET.fromstring(response.content)
            
            # Namespace untuk RSS
            ns = {'ht': 'https://trends.google.com/trending/rss'}
            
            trends = []
            
            # Parse setiap item
            for item in root.findall('.//item'):
                title = item.find('title').text.strip()
                
                # Ambil traffic (ht:approx_traffic)
                traffic = item.find('.//{https://trends.google.com/trending/rss}approx_traffic')
                traffic_count = traffic.text if traffic is not None else ""
                
                # Dapatkan tanggal publikasi
                pub_date = item.find('pubDate').text.strip()
                
                # Dapatkan berita terkait
                news_items = item.findall('.//{https://trends.google.com/trending/rss}news_item')
                related_news = []
                
                for news in news_items:
                    news_title = news.find('.//{https://trends.google.com/trending/rss}news_item_title')
                    news_url = news.find('.//{https://trends.google.com/trending/rss}news_item_url')
                    news_source = news.find('.//{https://trends.google.com/trending/rss}news_item_source')
                    
                    if news_title is not None and news_url is not None:
                        related_news.append({
                            'title': news_title.text,
                            'url': news_url.text,
                            'source': news_source.text if news_source is not None else ""
                        })
                
                # Format tanggal
                try:
                    date_obj = datetime.strptime(pub_date, '%a, %d %b %Y %H:%M:%S %z')
                    formatted_date = date_obj.strftime('%Y-%m-%d %H:%M')
                except:
                    formatted_date = pub_date
                
                trends.append({
                    'title': title,
                    'traffic': traffic_count,
                    'pub_date': pub_date,
                    'formatted_date': formatted_date,
                    'related_news': related_news
                })
            
            return trends
        
        except Exception as e:
            print(f"Error saat mengambil RSS feed: {e}")
            return []
    
    def get_web_trends_data(self, max_trends=50):
        """
        Mengambil data lengkap dari halaman web Google Trends menggunakan Selenium.
        
        Parameters:
        -----------
        max_trends : int
            Jumlah maksimum trending topics yang akan diambil
            
        Returns:
        --------
        list
            Daftar trending topics dengan informasi lengkap
        """
        try:
            # Setup Chrome options
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            
            # Inisialisasi driver
            driver = webdriver.Chrome(options=chrome_options)
            driver.get(self.web_url)
            
            # Tunggu sampai elemen trending tersedia
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='listitem']"))
            )
            
            # Tunggu sedikit lebih lama untuk memastikan semua data dimuat
            time.sleep(3)
            
            # Scroll halaman untuk memuat lebih banyak trending topics
            last_height = driver.execute_script("return document.body.scrollHeight")
            trends_collected = 0
            max_scroll_attempts = 10
            scroll_attempts = 0
            
            while trends_collected < max_trends and scroll_attempts < max_scroll_attempts:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)  # Berikan waktu untuk load
                
                # Hitung jumlah trends yang sudah dimuat
                trends_elements = driver.find_elements(By.CSS_SELECTOR, "div[role='listitem']")
                trends_collected = len(trends_elements)
                
                # Periksa apakah sudah mencapai akhir
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    scroll_attempts += 1
                else:
                    scroll_attempts = 0
                    last_height = new_height
                
                print(f"Collected {trends_collected} trends so far...")
                
                if trends_collected >= max_trends:
                    break
            
            # Ambil data dari halaman
            trends_data = []
            
            # Ambil semua item trending
            trend_items = driver.find_elements(By.CSS_SELECTOR, "div[role='listitem']")
            
            for i, item in enumerate(trend_items[:max_trends], 1):
                try:
                    # Judul trend
                    title = item.find_element(By.CSS_SELECTOR, "div.title").text
                    
                    # Volume pencarian
                    search_volume_element = item.find_element(By.CSS_SELECTOR, "div.search-count-title")
                    search_volume = search_volume_element.text
                    
                    # Waktu mulai trending
                    started_element = item.find_element(By.CSS_SELECTOR, "div.summary-text")
                    started = started_element.text
                    
                    # Status (active atau tidak)
                    status_element = item.find_elements(By.CSS_SELECTOR, "span.up")
                    status = "Active" if len(status_element) > 0 else "Inactive"
                    
                    # Kenaikan persentase
                    percentage_element = item.find_elements(By.CSS_SELECTOR, "div.change-value")
                    percentage = percentage_element[0].text if len(percentage_element) > 0 else ""
                    
                    # Berita terkait
                    related_news = []
                    news_elements = item.find_elements(By.CSS_SELECTOR, "a.article")
                    for news in news_elements:
                        news_title = news.find_element(By.CSS_SELECTOR, "div.article-title").text
                        news_source = news.find_element(By.CSS_SELECTOR, "div.source-and-time").text
                        news_url = news.get_attribute("href")
                        related_news.append({
                            'title': news_title,
                            'source': news_source,
                            'url': news_url
                        })
                    
                    trends_data.append({
                        'rank': i,
                        'title': title,
                        'search_volume': search_volume,
                        'started': started,
                        'status': status,
                        'percentage': percentage,
                        'related_news': related_news
                    })
                
                except Exception as e:
                    print(f"Error saat mengambil data untuk item {i}: {e}")
            
            driver.quit()
            return trends_data
        
        except Exception as e:
            print(f"Error saat scraping halaman Google Trends: {e}")
            if 'driver' in locals():
                driver.quit()
            return []
    
    def combine_data(self, rss_data, web_data):
        """
        Menggabungkan data dari RSS dan web scraping.
        
        Parameters:
        -----------
        rss_data : list
            Data dari RSS feed
        web_data : list
            Data dari web scraping
            
        Returns:
        --------
        list
            Data gabungan
        """
        combined_data = []
        
        # Buat dictionary dari data web dengan judul sebagai kunci
        web_dict = {item['title'].lower(): item for item in web_data}
        
        # Prioritaskan data RSS, tambahkan info dari web jika ada
        for rss_item in rss_data:
            title = rss_item['title'].lower()
            combined_item = rss_item.copy()
            
            if title in web_dict:
                web_item = web_dict[title]
                combined_item.update({
                    'rank': web_item['rank'],
                    'search_volume': web_item['search_volume'],
                    'started': web_item['started'],
                    'status': web_item['status'],
                    'percentage': web_item['percentage']
                })
            
            combined_data.append(combined_item)
        
        # Tambahkan data web yang tidak ada di RSS
        rss_titles = [item['title'].lower() for item in rss_data]
        for web_item in web_data:
            if web_item['title'].lower() not in rss_titles:
                web_item['traffic'] = web_item['search_volume']
                web_item['pub_date'] = datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0000')
                web_item['formatted_date'] = datetime.now().strftime('%Y-%m-%d %H:%M')
                combined_data.append(web_item)
        
        # Urutkan berdasarkan peringkat
        combined_data.sort(key=lambda x: x.get('rank', 999))
        
        return combined_data
    
    def get_complete_trends(self, max_trends=50):
        """
        Mendapatkan data trending topics lengkap dengan menggabungkan RSS dan web.
        
        Parameters:
        -----------
        max_trends : int
            Jumlah maksimum trending topics yang akan diambil
            
        Returns:
        --------
        list
            Daftar lengkap trending topics
        """
        print("Mengambil data dari RSS feed...")
        rss_data = self.get_rss_trends()
        
        print("Mengambil data dari halaman web Google Trends...")
        web_data = self.get_web_trends_data(max_trends)
        
        print("Menggabungkan data...")
        combined_data = self.combine_data(rss_data, web_data)
        
        # Batasi jumlah data sesuai max_trends
        return combined_data[:max_trends]
    
    def save_to_csv(self, trends_data, filename="google_trends_complete.csv"):
        """
        Menyimpan trending topics ke file CSV.
        
        Parameters:
        -----------
        trends_data : list
            Daftar trending topics
        filename : str
            Nama file CSV untuk menyimpan data
            
        Returns:
        --------
        pandas.DataFrame
            DataFrame berisi trending topics
        """
        if not trends_data:
            print("Tidak ada data untuk disimpan")
            return None
        
        # Flatten data untuk CSV (tanpa nested lists)
        flattened_data = []
        
        for item in trends_data:
            flat_item = {
                'rank': item.get('rank', ''),
                'title': item.get('title', ''),
                'traffic': item.get('traffic', ''),
                'search_volume': item.get('search_volume', ''),
                'started': item.get('started', ''),
                'status': item.get('status', ''),
                'percentage': item.get('percentage', ''),
                'formatted_date': item.get('formatted_date', '')
            }
            
            # Tambahkan URL berita terkait
            if 'related_news' in item and item['related_news']:
                flat_item['news_title_1'] = item['related_news'][0].get('title', '') if len(item['related_news']) > 0 else ''
                flat_item['news_source_1'] = item['related_news'][0].get('source', '') if len(item['related_news']) > 0 else ''
                flat_item['news_url_1'] = item['related_news'][0].get('url', '') if len(item['related_news']) > 0 else ''
                
                if len(item['related_news']) > 1:
                    flat_item['news_title_2'] = item['related_news'][1].get('title', '')
                    flat_item['news_source_2'] = item['related_news'][1].get('source', '')
                    flat_item['news_url_2'] = item['related_news'][1].get('url', '')
            
            flattened_data.append(flat_item)
        
        df = pd.DataFrame(flattened_data)
        df.to_csv(filename, index=False, encoding='utf-8')
        print(f"Data berhasil disimpan ke {filename}")
        
        return df
    
    def create_visualization(self, trends_data, save_path="google_trends_visualization.png"):
        """
        Membuat visualisasi trending topics.
        
        Parameters:
        -----------
        trends_data : list
            Daftar trending topics
        save_path : str
            Path untuk menyimpan gambar
        """
        if not trends_data:
            print("Tidak ada data untuk divisualisasikan")
            return
        
        # Ambil 20 teratas untuk visualisasi
        top_trends = trends_data[:20]
        
        # Extract tanggal untuk judul
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        # Konversi traffic ke numerik
        def extract_numeric(traffic_str):
            if not traffic_str or isinstance(traffic_str, (int, float)):
                return 0
            match = re.search(r'(\d+)', str(traffic_str))
            if match:
                return int(match.group(1))
            return 0
        
        # Siapkan data untuk plotting
        titles = [item['title'] for item in top_trends]
        traffic = [extract_numeric(item.get('traffic', 0)) for item in top_trends]
        
        # Set style
        plt.figure(figsize=(14, 10))
        sns.set_style("whitegrid")
        
        # Buat bar chart
        colors = sns.color_palette("viridis", len(titles))
        bars = plt.barh(range(len(titles)), traffic, color=colors)
        
        # Tambahkan labels
        plt.yticks(range(len(titles)), titles)
        plt.xlabel('Traffic (Jumlah Pencarian)')
        plt.title(f'Top {len(top_trends)} Trending Topics di Google Indonesia - {current_date}')
        
        # Tambahkan nilai di bar
        for i, (bar, value) in enumerate(zip(bars, traffic)):
            plt.text(value + max(traffic) * 0.01, bar.get_y() + bar.get_height()/2, 
                     f"{value}+", va='center')
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300)
        print(f"Visualisasi disimpan di {save_path}")
        plt.close()

# Contoh penggunaan
if __name__ == "__main__":
    scraper = GoogleTrendsCompleteData()
    
    # Dapatkan data lengkap (default: 50 teratas)
    print("Mengambil data trending di Google Indonesia...")
    complete_trends = scraper.get_complete_trends(max_trends=50)
    
    if complete_trends:
        print(f"\nBerhasil mengambil {len(complete_trends)} trending topics.")
        
        # Tampilkan 10 trending topics teratas
        print("\nTop 10 Trending Topics di Google Indonesia:")
        for i, trend in enumerate(complete_trends[:10], 1):
            search_volume = f" (search volume: {trend.get('search_volume', trend.get('traffic', 'Unknown'))})"
            started = f", {trend.get('started', '')}" if 'started' in trend else ""
            print(f"{i}. {trend['title']}{search_volume}{started}")
        
        # Simpan ke CSV
        df = scraper.save_to_csv(complete_trends)
        
        # Buat visualisasi
        scraper.create_visualization(complete_trends)
    else:
        print("Gagal mengambil trending topics.")