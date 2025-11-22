import os
import google.generativeai as genai
from dotenv import load_dotenv

# .env dosyasındaki API Key'i yükle
load_dotenv()

# API'yi yapılandır
api_key = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=api_key)

model = genai.GenerativeModel('gemini-2.5-flash')


def get_sql_from_llm(schema_info, user_question):

    """
    Tablo şemasını ve kullanıcı sorusunu alır, SQL sorgusu döndürür.
    """

    prompt = f"""
    Sen uzman bir Veri Analistisin ve SQLite konusunda özelleştin.

    GÖREVİN:
    Aşağıdaki tablo şemasına ve kullanıcı sorusuna dayanarak geçerli bir SQL sorgusu yaz.

    KURALLAR:
    1. Tablo adı her zaman: 'uploaded_data'
    2. Sadece ve sadece SQL kodunu döndür. Açıklama yapma.
    3. Markdown formatı (```sql ... ```) kullanma, sadece ham kod ver.

    VERİ ŞEMASI:
    {schema_info}

    KULLANICI SORUSU:
    {user_question}
    """

    try:
        response = model.generate_content(prompt)
        sql_query = response.text.strip()

        # Markdown kaldıysa temizleme
        sql_query = sql_query.replace("```sql", "").replace("```", "").strip()
        return sql_query

    except Exception as e:
        print(f"LLM Hatası: {e}")
        return None


def summarize_results(user_question, sql_query, result_df):

    """
    SQL sonucunu (Dataframe) alır ve kullanıcıya sözel açıklama yapar.
    """

    # Dataframe'i LLM'in okuyabilmesi için string formatına çevir
    data_preview = result_df.to_string()

    prompt = f"""
    Kullanıcı şu soruyu sordu: "{user_question}"

    Çalıştırılan SQL: "{sql_query}"

    Veritabanından dönen sonuç tablosu:
    {data_preview}

    GÖREVİN:
    Bu sonuçları kullanıcıya profesyonel ve net bir cümleyle açıkla. 
    Sayısal değerleri vurgula. Eğer sonuç boşsa "Veri bulunamadı" de.
    """

    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return "Sonuçları özetlerken bir hata oluştu."