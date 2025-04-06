import pandas as pd
from pytrends.request import TrendReq
import time
import matplotlib.pyplot as plt
import seaborn as sns

def get_simple_trends(keyword, timeframe='today 12-m', geo='ID'):
    """
    Fungsi sederhana untuk mendapatkan data trend untuk satu keyword.
    
    Parameters:
    -----------
    keyword : str
        Keyword yang ingin dicari
    timeframe : str
        Rentang waktu
    geo : str
        Kode negara (ID untuk Indonesia)
        
    Returns:
    --------
    pandas.DataFrame
        Data interest over time
    """
    try:
        # Inisialisasi pytrends dengan delay
        pytrends = TrendReq(hl='id-ID', tz=420, retries=3, backoff_factor=0.5)
        
        # Gunakan satu keyword saja untuk menghindari masalah
        pytrends.build_payload([keyword], cat=0, timeframe=timeframe, geo=geo)
        
        # Coba ambil data interest over time
        interest_df = pytrends.interest_over_time()
        
        if interest_df.empty:
            print(f"Tidak ada data untuk keyword: {keyword}")
            return None
            
        return interest_df
    
    except Exception as e:
        print(f"Error saat mengambil data untuk '{keyword}': {e}")
        return None

def plot_trend(trend_df, keyword, save_path='./'):
    """
    Plot data trend.
    
    Parameters:
    -----------
    trend_df : pandas.DataFrame
        Data trend dari get_simple_trends
    keyword : str
        Keyword yang dicari
    save_path : str
        Path untuk menyimpan hasil
    """
    if trend_df is None or trend_df.empty:
        print("Tidak ada data untuk diplot")
        return
        
    plt.figure(figsize=(12, 6))
    
    # Plot data
    sns.lineplot(data=trend_df[keyword], color='blue')
    
    plt.title(f'Minat Pencarian untuk "{keyword}" di Indonesia')
    plt.xlabel('Tanggal')
    plt.ylabel('Minat Relatif')
    plt.tight_layout()
    
    filename = f"{save_path}trend_{keyword.replace(' ', '_')}.png"
    plt.savefig(filename)
    print(f"Plot disimpan di {filename}")
    
    # Simpan data ke CSV
    csv_filename = f"{save_path}trend_{keyword.replace(' ', '_')}.csv"
    trend_df.to_csv(csv_filename)
    print(f"Data disimpan di {csv_filename}")
    
    # Tampilkan ringkasan data
    print("\nRingkasan statistik:")
    print(trend_df[keyword].describe())

# Contoh penggunaan
if __name__ == "__main__":
    # Daftar keyword untuk dicoba
    keywords = ["pemilu", "pilpres", "inflasi", "piala dunia", "teknologi"]
    
    for keyword in keywords:
        print(f"\nMengambil data trend untuk '{keyword}'...")
        trend_data = get_simple_trends(keyword)
        
        if trend_data is not None:
            plot_trend(trend_data, keyword)
            # Tunggu sebentar antara requests untuk menghindari rate limiting
            time.sleep(5)  
