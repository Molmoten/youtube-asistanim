import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi
from google import genai
import json
import datetime

# API Anahtarını buraya yapıştırıyoruz
API_KEY = st.secrets["GEMINI_API_KEY"]

st.title("YouTube Asistanım 🤖")
st.write("Zamanınız değerlidir. Yapay zeka ile izleme alışkanlıklarınızı ve videoları analiz edin.")

# --- 1. BÖLÜM: GEÇMİŞ ANALİZİ ---
st.header("📅 Gelişmiş Geçmiş Analizi")
yuklenen_dosya = st.file_uploader("Google Takeout 'watch-history.json' dosyasını buraya yükleyin:", type=['json'])

if yuklenen_dosya is not None:
    gecmis_verisi = json.load(yuklenen_dosya)
    st.success(f"Dosya yüklendi! Toplam {len(gecmis_verisi)} adet aktivite kaydı bulundu.")
    
    secenek = st.radio(
        "Nasıl bir analiz yapmak istersiniz?",
        ["Tek Bir Gün", "Belirli Bir Tarih Aralığı", "Tüm Geçmiş"]
    )
    
    filtrelenmis_videolar = []
    analiz_baslik = ""
    analizi_baslat = False
    
    if secenek == "Tek Bir Gün":
        secilen_tarih = st.date_input("Analiz etmek istediğiniz günü seçin:", datetime.date.today())
        if st.button("Günü Analiz Et"):
            analiz_baslik = f"{secilen_tarih} Tarihinin Analizi"
            analizi_baslat = True
            aranan_tarih_metni = str(secilen_tarih)
            for video in gecmis_verisi:
                if "time" in video and aranan_tarih_metni in video["time"]:
                    if "titleUrl" in video and "watch?v=" in video["titleUrl"]:
                        if "title" in video:
                            temiz_baslik = video["title"].replace("Watched ", "").replace("İzlediniz: ", "")
                            filtrelenmis_videolar.append(temiz_baslik)
                            
    elif secenek == "Belirli Bir Tarih Aralığı":
        col1, col2 = st.columns(2)
        with col1:
            baslangic_tarihi = st.date_input("Başlangıç Tarihi:", datetime.date.today() - datetime.timedelta(days=7))
        with col2:
            bitis_tarihi = st.date_input("Bitiş Tarihi:", datetime.date.today())
        if st.button("Aralığı Analiz Et"):
            analiz_baslik = f"{baslangic_tarihi} ile {bitis_tarihi} Arası Analiz"
            analizi_baslat = True
            for video in gecmis_verisi:
                if "time" in video:
                    try:
                        video_tarihi_str = video["time"][:10]
                        video_tarihi = datetime.datetime.strptime(video_tarihi_str, "%Y-%m-%d").date()
                        if baslangic_tarihi <= video_tarihi <= bitis_tarihi:
                            if "titleUrl" in video and "watch?v=" in video["titleUrl"]:
                                if "title" in video:
                                    temiz_baslik = video["title"].replace("Watched ", "").replace("İzlediniz: ", "")
                                    filtrelenmis_videolar.append(temiz_baslik)
                    except Exception:
                        pass
                        
    elif secenek == "Tüm Geçmiş":
        st.info("Tüm geçmiş analizinde en son izlediğiniz 1000 video baz alınacaktır.")
        if st.button("Tüm Geçmişi Analiz Et"):
            analiz_baslik = "Tüm Geçmişin Analizi (Son 1000 Video)"
            analizi_baslat = True
            for video in gecmis_verisi:
                if "titleUrl" in video and "watch?v=" in video["titleUrl"]:
                    if "title" in video:
                        temiz_baslik = video["title"].replace("Watched ", "").replace("İzlediniz: ", "")
                        filtrelenmis_videolar.append(temiz_baslik)
            if len(filtrelenmis_videolar) > 1000:
                filtrelenmis_videolar = filtrelenmis_videolar[:1000]

    if analizi_baslat:
        if len(filtrelenmis_videolar) == 0:
            st.warning("Seçtiğiniz kriterlere uygun video bulunamadı.")
        else:
            st.success(f"Seçilen aralıkta toplam **{len(filtrelenmis_videolar)}** adet gerçek video bulundu.")
            videolar_metni = "\n".join(filtrelenmis_videolar)
            try:
                client = genai.Client(api_key=API_KEY)
                gunluk_talimat = f"""
                Sen dürüst ve motive edici bir eğitim koçusun. Karşındaki kişi YKS'ye hazırlanan 12. sınıf bir öğrenci.
                Aşağıdaki video listesini incele ({analiz_baslik}) ve kısa bir özet ile koç yorumu yap.
                İşte liste:
                {videolar_metni}
                """
                cevap_gunluk = client.models.generate_content(model='gemini-2.5-flash', contents=gunluk_talimat)
                st.subheader(f"📊 Analiz Karnesi ({secenek}):")
                st.write(cevap_gunluk.text)
                with st.expander("İzlediğiniz Videoların Tam Listesini Görün"):
                    for i, baslik in enumerate(filtrelenmis_videolar):
                        st.write(f"**{i+1}.** {baslik}")
            except Exception as e:
                st.error("Analiz sırasında bir hata oluştu:")
                st.warning(e)

st.divider()

# --- 2. BÖLÜM: TEK VİDEO VE CANLI TÜRKÇE ALTYAZI OYNATICI ---
st.header("🔍 Akıllı Video Oynatıcı ve Altyazı Çevirici")
video_linki = st.text_input("İzlemek ve altyazısını çevirmek istediğiniz YouTube linkini yapıştırın:")

if video_linki:
    if "v=" in video_linki:
        video_id = video_linki.split("v=")[1][:11]
    elif "youtu.be/" in video_linki:
        video_id = video_linki.split("youtu.be/")[1][:11]
    else:
        video_id = ""

    if video_id:
        st.video(video_linki)
        st.subheader("🔤 Türkçe Altyazı Akışı")
        
        try:
            # HATAYI ÇÖZDÜĞÜMÜZ TEMİZ BLOK
            mevcut_altyazilar = YouTubeTranscriptApi.list_transcripts(video_id)
            
            try:
                # Önce orijinal Türkçe var mı diye bakar
                secilen_altyazi = mevcut_altyazilar.find_transcript(['tr'])
                altyazilar = secilen_altyazi.fetch()
                st.caption("💡 Bu videoda orijinal Türkçe altyazı bulundu.")
            except Exception:
                # Orijinal Türkçe yoksa, bulduğu İLK altyazıyı (İngilizce vs.) alır ve Türkçeye çevirir
                for altyazi in mevcut_altyazilar:
                    altyazilar = altyazi.translate('tr').fetch()
                    st.caption(f"🤖 Orijinal Türkçe bulunamadı. '{altyazi.language}' dilindeki altyazı otomatik olarak Türkçeye çevrildi.")
                    break # Çeviriyi yaptıktan sonra döngüyü durdurur

            def zaman_formatla(saniye):
                sure = datetime.timedelta(seconds=int(saniye))
                return str(sure)[2:] if int(saniye) < 3600 else str(sure)

            st.write("---")
            for parca in altyazilar:
                metin = parca['text'] if isinstance(parca, dict) else parca.text
                baslangic = parca['start'] if isinstance(parca, dict) else parca.start
                st.write(f"`[{zaman_formatla(baslangic)}]` : {metin}")

        except Exception as e:
            st.warning("⚠️ Bu videoda teknik olarak çekilebilecek bir altyazı akışı bulunamadı (Shorts veya altyazısı kapalı video olabilir).")
            st.info("🤖 Ancak yapay zekamız videoyu sizin için yine de analiz ediyor, lütfen bekleyin...")
            
            try:
                client = genai.Client(api_key=API_KEY)
                yedek_talimat = f"""
                Şu YouTube videosunun linki: {video_linki}
                Eğer bu videonun içeriğini internetten biliyorsan dürüstçe Türkçe özetle. 
                Eğer videoyu gerçekten bilmiyorsan, uydurmak yerine kesinlikle "Bu videonun içeriğine erişemiyorum" de.
                """
                cevap_yedek = client.models.generate_content(model='gemini-2.5-flash', contents=yedek_talimat)
                st.subheader("🧠 Yapay Zeka Genel Video Analizi (Altyazısız Mod):")
                st.write(cevap_yedek.text)
            except Exception as yedek_hata:
                st.error("Yapay zeka analiz ederken bir hata yaşandı:")
                st.warning(yedek_hata)