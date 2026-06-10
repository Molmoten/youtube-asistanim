import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi
from google import genai
import json
import datetime

# Şifremizi Streamlit'in güvenli kasasından çekiyoruz
API_KEY = st.secrets["GEMINI_API_KEY"]

st.set_page_config(page_title="YouTube Asistanım", page_icon="🤖", layout="wide")

st.title("YouTube Asistanım 🤖")
st.write("Zamanınız değerlidir. Yapay zeka ile izleme alışkanlıklarınızı yönetin ve videoları analiz edin.")

# UYGULAMAYI 3 ŞIK SEKMEYE BÖLÜYORUZ
sekme1, sekme2, sekme3 = st.tabs(["📅 Geçmiş Analizi", "🧠 Video Değer Analizi", "🔤 Akıllı Altyazı & Oynatıcı"])

# --- 1. SEKME: GEÇMİŞ ANALİZİ ---
with sekme1:
    st.header("Günlük ve Tarihsel Analiz")
    yuklenen_dosya = st.file_uploader("Google Takeout 'watch-history.json' dosyasını yükleyin:", type=['json'])

    if yuklenen_dosya is not None:
        gecmis_verisi = json.load(yuklenen_dosya)
        st.success(f"Dosya yüklendi! Toplam {len(gecmis_verisi)} kayıt bulundu.")
        
        secenek = st.radio("Analiz Tipi:", ["Tek Bir Gün", "Belirli Bir Tarih Aralığı", "Tüm Geçmiş"])
        
        filtrelenmis_videolar = []
        analiz_baslik = ""
        analizi_baslat = False
        
        if secenek == "Tek Bir Gün":
            secilen_tarih = st.date_input("Analiz edilecek günü seçin:", datetime.date.today())
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
                        except:
                            pass
                            
        elif secenek == "Tüm Geçmiş":
            st.info("Sistem yorulmasın diye son 1000 video baz alınacaktır.")
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
                st.warning("Seçilen aralıkta video bulunamadı.")
            else:
                st.success(f"Toplam **{len(filtrelenmis_videolar)}** video analiz ediliyor...")
                videolar_metni = "\n".join(filtrelenmis_videolar)
                try:
                    client = genai.Client(api_key=API_KEY)
                    gunluk_talimat = f"""
                    Sen motive edici bir eğitim koçusun. Karşındaki kişi YKS'ye hazırlanan 12. sınıf öğrencisi.
                    Şu video listesini incele ({analiz_baslik}): {videolar_metni}
                    Kısa bir özet ve sınava hazırlık bağlamında net bir koç yorumu yap.
                    """
                    # Kotası geniş olan 1.5 modeli kullanılıyor
                    cevap_gunluk = client.models.generate_content(model='gemini-1.5-flash', contents=gunluk_talimat)
                    st.write(cevap_gunluk.text)
                    with st.expander("Tam Listeyi Gör"):
                        for i, baslik in enumerate(filtrelenmis_videolar):
                            st.write(f"**{i+1}.** {baslik}")
                except Exception as e:
                    st.error(f"Hata: {e}")

# --- 2. SEKME: VİDEO DEĞER ANALİZİ (İzlenir mi?) ---
with sekme2:
    st.header("Bu Video İzlemeye Değer Mi?")
    analiz_linki = st.text_input("Analiz edilecek YouTube linkini yapıştırın:")
    
    if st.button("Videoyu Değerlendir"):
        if analiz_linki:
            video_id = ""
            if "v=" in analiz_linki: video_id = analiz_linki.split("v=")[1][:11]
            elif "youtu.be/" in analiz_linki: video_id = analiz_linki.split("youtu.be/")[1][:11]
            
            if video_id:
                with st.spinner("Videonun içeriği okunuyor..."):
                    try:
                        mevcut_altyazilar = YouTubeTranscriptApi.list_transcripts(video_id)
                        altyazilar = None
                        
                        try:
                            altyazilar = mevcut_altyazilar.find_transcript(['tr']).fetch()
                        except:
                            for altyazi in mevcut_altyazilar:
                                if altyazi.is_translatable:
                                    altyazilar = altyazi.translate('tr').fetch()
                                    break
                                    
                        if altyazilar:
                            tam_metin = " ".join([parca['text'] if isinstance(parca, dict) else parca.text for parca in altyazilar])
                            
                            st.success("İçerik başarıyla okundu. Yapay zeka değerlendiriyor...")
                            client = genai.Client(api_key=API_KEY)
                            talimat = f"""
                            Sen analitik bir asistansın. Karşındaki kişi YKS'ye hazırlanan 12. sınıf öğrencisi.
                            Şu YouTube videosunun metnini incele: {tam_metin}
                            1. Ana konu nedir?
                            2. Sınav senesindeki bir öğrenci için bu videoyu izlemek değerli midir yoksa zaman kaybı mıdır? Net bir tavsiye ver.
                            """
                            # Kotası geniş olan 1.5 modeli kullanılıyor
                            cevap = client.models.generate_content(model='gemini-1.5-flash', contents=talimat)
                            st.write(cevap.text)
                        else:
                            st.warning("Bu videoda okunabilecek bir metin (altyazı) yok. Uydurma yapmamak için analiz edilemiyor.")
                    except:
                        st.warning("Bu videonun altyazıları tamamen kapalı veya bu bir Shorts videosu. Analiz yapılamıyor.")

# --- 3. SEKME: AKILLI ALTYAZI ÇEVİRİCİ ---
with sekme3:
    st.header("Video Oynatıcı ve Canlı Çeviri")
    izleme_linki = st.text_input("İzlemek ve altyazısını okumak istediğiniz linki yapıştırın:")
    
    if izleme_linki:
        video_id = ""
        if "v=" in izleme_linki: video_id = izleme_linki.split("v=")[1][:11]
        elif "youtu.be/" in izleme_linki: video_id = izleme_linki.split("youtu.be/")[1][:11]
        
        if video_id:
            st.video(izleme_linki)
            st.subheader("🔤 Türkçe Altyazı Akışı (Yapay Zeka Analizi Yok)")
            
            try:
                mevcut_altyazilar = YouTubeTranscriptApi.list_transcripts(video_id)
                altyazilar = None
                
                try:
                    secilen_altyazi = mevcut_altyazilar.find_transcript(['tr'])
                    altyazilar = secilen_altyazi.fetch()
                    st.caption("💡 Orijinal Türkçe altyazı bulundu.")
                except:
                    for altyazi in mevcut_altyazilar:
                        if altyazi.is_translatable:
                            altyazilar = altyazi.translate('tr').fetch()
                            st.caption(f"🤖 Orijinal Türkçe bulunamadı. '{altyazi.language}' dilinden otomatik çevrildi.")
                            break
                            
                if altyazilar:
                    def zaman_formatla(saniye):
                        sure = datetime.timedelta(seconds=int(saniye))
                        return str(sure)[2:] if int(saniye) < 3600 else str(sure)

                    for parca in altyazilar:
                        metin = parca['text'] if isinstance(parca, dict) else parca.text
                        baslangic = parca['start'] if isinstance(parca, dict) else parca.start
                        st.write(f"`[{zaman_formatla(baslangic)}]` : {metin}")
                else:
                    st.warning("Çevrilecek altyazı bulunamadı.")
            except:
                st.warning("Bu videoda teknik olarak çekilebilecek bir altyazı yok.")