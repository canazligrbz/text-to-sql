import sqlite3
import pandas as pd

def get_db_connection():
    """
    Geçici (RAM üzerinde) bir veritabanı bağlantısı oluşturur
    """
    conn = sqlite3.connect(':memory:', check_same_thread=False)
    return conn


def load_data_to_db(conn, df):
    """
    Pandas DataFrame'ini SQLite tablosuna yazar.
    Manuel DROP işlemi ile kilitlenme sorunlarını çözer.
    """
    try:
        cursor = conn.cursor()

        # Eğer tablo silinmediyse manuel sil
        cursor.execute("DROP TABLE IF EXISTS uploaded_data")
        conn.commit()  # İşlemi onayla

        # Kolon İsimlerini Temizle
        df.columns = df.columns.str.strip().str.replace(' ', '_').str.replace(r'[^\w]', '', regex=True)

        # Veriyi Yükle
        # chunksize=500, büyük verilerde hata almayı engellemesi için
        df.to_sql(
            'uploaded_data',
            conn,
            index=False,
            if_exists='replace',
            chunksize=500
        )
        return True

    except Exception as e:
        print(f"Veri yükleme hatası: {e}")
        return False


def get_table_schema(conn):
    """
    Tablonun kolon isimlerini ve tiplerini metin olarak döndürür.
    LLM'in tabloyu tanıması için bu gereklidir.
    """
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(uploaded_data)")
    columns = cursor.fetchall()

    # Örnek çıktı: cid, name, type, notnull, dflt_value, pk
    schema_str = ""
    for col in columns:
        schema_str += f"- Kolon: {col[1]} (Tip: {col[2]})\n"

    return schema_str


def execute_query(conn, query):
    """
    SQL sorgusunu çalıştırır ve sonucu DataFrame olarak döndürür.
    """
    try:
        result_df = pd.read_sql_query(query, conn)
        return result_df
    except Exception as e:
        return str(e)  # Hatayı string olarak döndür