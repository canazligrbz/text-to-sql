import streamlit as st
import pandas as pd
from src.db_manager import get_db_connection, load_data_to_db, get_table_schema, execute_query
from src.llm_manager import get_sql_from_llm, summarize_results

# Sayfa Ayarları
st.set_page_config(page_title="AI Data Analyst", page_icon="📊", layout="centered")

def main():
    st.title("📊 AI Data Analyst")
    st.markdown("CSV dosyanı yükle ve verilerinle sohbet etmeye başla!")

    # 1. Session State Başlatma (Veritabanı bağlantısını hafızada tutmak için)
    if 'conn' not in st.session_state:
        st.session_state.conn = get_db_connection()
    if 'data_loaded' not in st.session_state:
        st.session_state.data_loaded = False

    # 2. Kenar Çubuğu (Dosya Yükleme)
    with st.sidebar:
        st.header("📂 Veri Yükleme")
        uploaded_file = st.file_uploader("CSV Dosyanızı Yükleyin", type=["csv"])

        # Dosya değişirse veya yeniden yüklenirse state'i sıfırla
        if uploaded_file:
            try:
                # Önce standart UTF-8 ile okumayı dene
                df = pd.read_csv(uploaded_file)
            except UnicodeDecodeError:
                # Hata verirse dosya imlecini başa sar
                uploaded_file.seek(0)
                # Alternatif encoding (latin1) ile dene
                df = pd.read_csv(uploaded_file, encoding='ISO-8859-1')
            except Exception as e:
                st.error(f"Beklenmedik bir hata: {e}")
                st.stop()

            try:
                # Kolon isimlerindeki boşlukları temizle
                df.columns = df.columns.str.replace(' ', '_')

                # Veriyi DB'ye yükle
                load_data_to_db(st.session_state.conn, df)
                st.session_state.data_loaded = True
                st.success("Veri Başarıyla Yüklendi! ✅")

                # Önizleme göster
                st.subheader("Veri Önizlemesi")
                st.dataframe(df.head(10))

            except Exception as e:
                st.error(f"Veri işleme hatası: {e}")

    # 3. Ana Ekran (Soru-Cevap)
    if st.session_state.data_loaded:
        # Kullanıcı sorusu
        question = st.text_area("Sorunuzu Yazın:", placeholder="Örn: En çok satış yapılan kategori hangisi?")

        if st.button("Analiz Et 🚀"):
            if question:
                with st.spinner('Yükleniyor...'):

                    # Şemayı al
                    schema = get_table_schema(st.session_state.conn)

                    # Gemini'den SQL kodu iste
                    sql_query = get_sql_from_llm(schema, question)

                    if sql_query:

                        # SQL Kodunu Görünür Hale Getiriyoruz
                        st.markdown("### 📝 Oluşturulan SQL Sorgusu")
                        st.code(sql_query, language='sql')

                        # SQL'i çalıştır
                        result_df = execute_query(st.session_state.conn, sql_query)

                        if isinstance(result_df, pd.DataFrame):
                            # Tablo sonucunu göster
                            st.write("### 🔢 Sonuç Tablosu")
                            st.dataframe(result_df)

                            # Sonucu yorumla
                            if not result_df.empty:
                                summary = summarize_results(question, sql_query, result_df)
                                st.info(f"💡 **AI Analizi:** {summary}")
                            else:
                                st.warning("Sorgu sonucunda veri bulunamadı.")
                        else:
                            st.error(f"SQL Çalıştırma Hatası: {result_df}")
                    else:
                        st.error("SQL kodu üretilemedi. Lütfen sorunuzu tekrar deneyin.")
            else:
                st.warning("Lütfen bir soru girin.")
    else:
        st.info("Lütfen başlamak için sol menüden bir CSV dosyası yükleyin.")


if __name__ == "__main__":
    main()