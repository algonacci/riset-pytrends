import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import re

def get_google_trends_indonesia(limit=None):
    """
    Fungsi sederhana untuk mengambil trending topics dari Google Trends Indonesia.
    
    Parameters:
    -----------
    limit : int, optional
        Batas jumlah trending topics yang akan diambil. None untuk mengambil semua.
    
    Returns:
    --------
    dict
        Dictionary berisi trending topics dengan format:
        {
            'date': 'YYYY-MM-DD',
            'trends': [
                {
                    'title': 'Judul trending',
                    'traffic': 'Jumlah traffic (contoh: 1000+)',
                    'pub_date': 'Tanggal publikasi',
                    'news_items': [
                        {
                            'title': 'Judul berita',
                            'url': 'URL berita',
                            'source': 'Sumber berita'
                        },
                        ...
                    ]
                },
                ...
            ]
        }
    """
    # URL Feed RSS Google Trends Indonesia
    rss_url = "https://trends.google.co.id/trending/rss?geo=ID"
    
    # Headers untuk request
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Accept": "application/rss+xml, application/xml, text/xml"
    }
    
    try:
        # Lakukan request ke RSS feed
        response = requests.get(rss_url, headers=headers)
        response.raise_for_status()
        
        # Parse XML
        root = ET.fromstring(response.content)
        
        # Namespace untuk tag custom di RSS feed
        namespaces = {
            'ht': 'https://trends.google.com/trending/rss'
        }
        
        trends = []
        current_date = None
        
        # Parse setiap item trending
        items = root.findall('.//item')
        
        # Batasi jumlah item jika limit ditentukan
        if limit is not None:
            items = items[:limit]
        
        for item in items:
            title_elem = item.find('title')
            link_elem = item.find('link')
            pubDate_elem = item.find('pubDate')
            
            # Ambil traffic count
            traffic_elem = item.find('.//{https://trends.google.com/trending/rss}approx_traffic')
            
            # Ambil gambar (picture)
            picture_elem = item.find('.//{https://trends.google.com/trending/rss}picture')
            picture_source_elem = item.find('.//{https://trends.google.com/trending/rss}picture_source')
            
            # Ambil berita terkait
            news_items_elem = item.findall('.//{https://trends.google.com/trending/rss}news_item')
            
            # Cek apakah elemen utama ada
            if title_elem is not None and title_elem.text:
                title = title_elem.text.strip()
                link = link_elem.text.strip() if link_elem is not None and link_elem.text else ""
                pub_date = pubDate_elem.text.strip() if pubDate_elem is not None and pubDate_elem.text else ""
                traffic = traffic_elem.text.strip() if traffic_elem is not None and traffic_elem.text else ""
                
                # Parse tanggal publikasi
                try:
                    date_obj = datetime.strptime(pub_date, '%a, %d %b %Y %H:%M:%S %z')
                    formatted_date = date_obj.strftime('%Y-%m-%d')
                    if current_date is None:
                        current_date = formatted_date
                except Exception as e:
                    formatted_date = ""
                
                # Parse berita terkait
                news_items = []
                for news_item in news_items_elem:
                    news_title = news_item.find('.//{https://trends.google.com/trending/rss}news_item_title')
                    news_url = news_item.find('.//{https://trends.google.com/trending/rss}news_item_url')
                    news_source = news_item.find('.//{https://trends.google.com/trending/rss}news_item_source')
                    
                    if news_title is not None and news_title.text and news_url is not None and news_url.text:
                        news_items.append({
                            'title': news_title.text.strip(),
                            'url': news_url.text.strip(),
                            'source': news_source.text.strip() if news_source is not None and news_source.text else ""
                        })
                
                # Tambahkan data trending topic
                trend_data = {
                    'title': title,
                    'traffic': traffic,
                    'pub_date': pub_date,
                    'news_items': news_items
                }
                
                # Tambahkan picture jika ada
                if picture_elem is not None and picture_elem.text:
                    trend_data['picture'] = picture_elem.text.strip()
                    if picture_source_elem is not None and picture_source_elem.text:
                        trend_data['picture_source'] = picture_source_elem.text.strip()
                
                trends.append(trend_data)
        
        # Hasil akhir
        result = {
            'date': current_date or datetime.now().strftime('%Y-%m-%d'),
            'trends': trends
        }
        
        return result
    
    except Exception as e:
        print(f"Error saat mengambil Google Trends: {e}")
        return {'date': datetime.now().strftime('%Y-%m-%d'), 'trends': []}

# Contoh penggunaan
if __name__ == "__main__":
    # Dapatkan trending topics (tanpa batasan jumlah)
    trends_data = get_google_trends_indonesia()
    
    # Cetak tanggal
    print(f"Google Trends Indonesia - {trends_data['date']}")
    
    # Cetak trending topics
    print("\nTop Trending Topics:")
    for i, trend in enumerate(trends_data['trends'], 1):
        traffic = f" ({trend['traffic']} pencarian)" if 'traffic' in trend else ""
        print(f"{i}. {trend['title']}{traffic}")
        
        # Cetak berita terkait untuk setiap trend
        if trend['news_items']:
            print("   Berita terkait:")
            for j, news in enumerate(trend['news_items'][:2], 1):  # Tampilkan 2 berita pertama saja
                print(f"   {j}. {news['title']} ({news['source']})")