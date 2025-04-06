# import pandas as pd                        
# from pytrends.request import TrendReq
# pytrend = TrendReq()
# # pytrend.build_payload(kw_list=['Taylor Swift'])
# # # Interest by Region
# # df = pytrend.interest_by_region()
# # print(df.head(10))
# # df = pytrend.trending_searches(pn='united_states')
# # print(df.head())
# # df = pytrend.today_searches(pn='US')
# # df = pytrend.top_charts(2019, hl='en-US', tz=300, geo='GLOBAL')
# # df.head()
# # print(df)
# related_topic = pytrend.related_topics()
# print(related_topic.values())



import pandas as pd
from pytrends.request import TrendReq
import datetime
import matplotlib.pyplot as plt
import seaborn as sns

def get_indonesia_trends(timeframe='now 1-d', geo='ID'):
    """
    Mengambil trending topics di Google Trends Indonesia.
    
    Parameters:
    -----------
    timeframe : str
        Jangka waktu untuk trend ('now 1-d', 'now 7-d', 'today 1-m', 'today 3-m', dll)
    geo : str
        Kode geografis (ID untuk Indonesia)
        
    Returns:
    --------
    pandas.DataFrame
        DataFrame berisi trending topics
    """
    # Inisialisasi pytrends
    pytrends = TrendReq(hl='id-ID', tz=420)  # tz=420 adalah GMT+7 (Waktu Indonesia Barat)
    
    # Dapatkan trending pencarian
    trending_searches_df = pytrends.trending_searches(pn=geo)
    trending_searches_df.columns = ['Trending Search']
    
    # Dapatkan trending saat ini (real time)
    try:
        trending_now = pytrends.trending_searches(pn=geo)
        trending_now.columns = ['Trending Now']
    except:
        trending_now = pd.DataFrame({'Trending Now': ['Data tidak tersedia']})
    
    # Buat timestamp untuk tracking
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    return {
        'trending_searches': trending_searches_df,
        'trending_now': trending_now,
        'timestamp': timestamp
    }

def get_trend_details(keywords, timeframe='today 1-m', geo='ID'):
    """
    Mendapatkan detail trend untuk keyword tertentu.
    
    Parameters:
    -----------
    keywords : list
        Daftar keyword yang ingin dilihat trendnya (max 5)
    timeframe : str
        Jangka waktu untuk trend
    geo : str
        Kode geografis (ID untuk Indonesia)
        
    Returns:
    --------
    dict
        Dictionary berisi detail trend
    """
    if len(keywords) > 5:
        keywords = keywords[:5]  # Google Trends membatasi 5 keyword
        
    # Inisialisasi pytrends
    pytrends = TrendReq(hl='id-ID', tz=420)
    
    # Build payload
    pytrends.build_payload(keywords, cat=0, timeframe=timeframe, geo=geo)
    
    # Dapatkan data interest over time
    interest_over_time_df = pytrends.interest_over_time()
    
    # Dapatkan data by region
    interest_by_region_df = pytrends.interest_by_region(resolution='COUNTRY', inc_low_vol=True)
    
    # Dapatkan related topics
    related_topics = pytrends.related_topics()
    
    # Dapatkan related queries
    related_queries = pytrends.related_queries()
    
    return {
        'interest_over_time': interest_over_time_df,
        'interest_by_region': interest_by_region_df,
        'related_topics': related_topics,
        'related_queries': related_queries
    }

def visualize_trends(trends_data):
    """
    Memvisualisasikan data trends.
    
    Parameters:
    -----------
    trends_data : dict
        Data trends dari fungsi get_trend_details
    """
    # Set style
    sns.set(style="whitegrid")
    
    # Plot interest over time
    plt.figure(figsize=(12, 6))
    trends_data['interest_over_time'].plot(figsize=(12, 6))
    plt.title('Interest Over Time')
    plt.xlabel('Date')
    plt.ylabel('Interest')
    plt.legend(title='Keywords')
    plt.tight_layout()
    plt.savefig('interest_over_time.png')
    
    # Simpan related queries ke CSV untuk analisis lebih lanjut
    for keyword, data in trends_data['related_queries'].items():
        if data['top'] is not None:
            data['top'].to_csv(f'related_queries_{keyword}_top.csv', index=False)
        if data['rising'] is not None:
            data['rising'].to_csv(f'related_queries_{keyword}_rising.csv', index=False)

def save_trends_to_csv(trends, filename='indonesia_trends.csv'):
    """
    Menyimpan data trends ke CSV.
    
    Parameters:
    -----------
    trends : dict
        Data trends dari fungsi get_indonesia_trends
    filename : str
        Nama file untuk menyimpan data
    """
    trends['trending_searches'].to_csv(f"trending_searches_{filename}", index=False)
    trends['trending_now'].to_csv(f"trending_now_{filename}", index=False)
    
    # Buat file log
    with open('trend_log.txt', 'a') as f:
        f.write(f"Data diambil pada: {trends['timestamp']}\n")
        f.write(f"Top trending: {trends['trending_searches'].iloc[0, 0]}\n")
        f.write("-" * 50 + "\n")

# Contoh penggunaan
if __name__ == "__main__":
    # Mengambil trending saat ini
    indonesia_trends = get_indonesia_trends(timeframe='now 1-d')
    
    print(f"Trending topics di Indonesia pada {indonesia_trends['timestamp']}:")
    print("\nTop 10 Trending Searches:")
    print(indonesia_trends['trending_searches'].head(10))
    
    # Simpan ke CSV
    save_trends_to_csv(indonesia_trends)
    
    # Ambil top 5 trend
    top_trends = indonesia_trends['trending_searches'].iloc[:5, 0].tolist()
    print(f"\nMenganalisis top 5 trend: {', '.join(top_trends)}")
    
    # Dapatkan detail untuk top 5 trend
    trend_details = get_trend_details(top_trends, timeframe='today 3-m')
    
    # Visualisasikan
    visualize_trends(trend_details)
    
    print("\nVisualisasi dan data tersimpan. Lihat interest_over_time.png dan file CSV untuk detail.")