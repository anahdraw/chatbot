import streamlit as st
import requests
import json

# Fungsi untuk memanggil endpoint Langflow (diperbarui)
def run_langflow_analysis(base_url, flow_id, bearer_token, company_names, openai_api_key=None):
    """
    Mengirim permintaan ke endpoint Langflow dengan URL yang dibangun secara dinamis.
    """
    # Membangun URL API yang benar
    # Ini adalah format standar untuk Langflow di DataStax Astra
    api_endpoint = f"{base_url.rstrip('/')}/api/v1/run/{flow_id}"

    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json"
    }
    
    # Payload yang akan dikirim. Strukturnya harus sesuai dengan flow Anda di Langflow.
    # Input utama dikirim melalui 'input_value'.
    # Ganti 'ChatInput-...' jika komponen input di flow Anda punya ID yang spesifik.
    payload = {
        "input_value": f"Lakukan riset pasar mendalam untuk perusahaan-perusahaan berikut: {', '.join(company_names)}. Berikan analisis tentang posisi pasar, kompetitor utama, kekuatan, kelemahan, dan potensi pertumbuhan mereka.",
        "output_type": "chat",
        "input_type": "chat",
        "tweaks": {
            # Contoh jika Anda perlu menimpa parameter komponen di dalam flow:
            # "OpenAI-XXXXX": {
            #     "openai_api_key": openai_api_key
            # }
        }
    }

    st.info(f"Mengirim permintaan ke URL: {api_endpoint}")
    # st.json(payload) # Hapus komentar ini jika Anda ingin melihat payload yang dikirim untuk debugging

    try:
        # Mengatur timeout yang lebih lama untuk proses LLM
        response = requests.post(api_endpoint, headers=headers, data=json.dumps(payload), timeout=300)
        response.raise_for_status()  # Akan memunculkan error jika status code bukan 2xx (seperti 404, 500, dll.)
        
        # Langflow biasanya mengembalikan hasil dalam format JSON tunggal, bukan streaming untuk endpoint ini
        result = response.json()
        
        # Ekstrak pesan dari output. Strukturnya bisa berbeda, jadi ini perlu disesuaikan.
        # Anda bisa menggunakan st.json(result) untuk melihat struktur lengkapnya saat pertama kali mencoba.
        # Jalur umum: result -> outputs -> [0] -> outputs -> [0] -> results -> message -> data -> text
        output = result.get("outputs", [{}])[0]
        final_text = output.get("outputs", [{}])[0].get("results", {}).get("message", {}).get("data", {}).get("text", "")
        
        if not final_text:
             st.warning("Berhasil terhubung, namun tidak ada teks yang bisa diekstrak dari respons. Mungkin struktur output flow Anda berbeda.")
             st.write("Struktur Respons Mentah dari Langflow:")
             st.json(result)

        return final_text

    except requests.exceptions.HTTPError as http_err:
        st.error(f"HTTP Error terjadi: {http_err}")
        st.error(f"Response Body: {http_err.response.text}")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Terjadi kesalahan saat menghubungi API Langflow: {e}")
        return None
    except json.JSONDecodeError:
        st.error("Gagal mem-parsing respons dari Langflow. Respons bukan format JSON yang valid.")
        st.text(response.text)
        return None


# --- UI Aplikasi Streamlit ---

st.set_page_config(page_title="Market Research AI", layout="wide")

st.title("🔬 Market Research Analysis dengan Langflow")
st.markdown("Aplikasi ini menggunakan alur kerja (flow) dari Langflow untuk melakukan riset pasar pada perusahaan pilihan Anda.")

# Sidebar untuk konfigurasi
with st.sidebar:
    st.header("⚙️ Konfigurasi Koneksi Langflow")
    langflow_base_url = st.text_input(
        "URL Dasar Langflow",
        placeholder="https://yourapp.datastax.com/...",
        help="Salin URL dasar dari aplikasi Langflow Anda di DataStax. Contoh: https://api.langflow.astra.datastax.com/lf/115811d4-..."
    )
    langflow_flow_id = st.text_input(
        "ID Flow Langflow",
        placeholder="5f371299-11e3-4175-b4ec-c980576bfd6b",
        help="Salin ID unik dari flow yang ingin Anda gunakan."
    )
    langflow_bearer = st.text_input(
        "Langflow Bearer Token", 
        type="password",
        help="Token API untuk otentikasi. Dapatkan dari menu 'API Keys' di Langflow."
    )
    st.markdown("---")
    openai_api_key = st.text_input(
        "OpenAI API Key (Opsional)", 
        type="password",
        help="Masukkan hanya jika flow Anda di Langflow membutuhkannya sebagai input/tweak."
    )

# Konten utama
st.header("Pilih Perusahaan untuk Dianalisis")

predefined_companies = [
    "Google (Alphabet)", "Microsoft", "Apple", "Amazon", "Meta (Facebook)",
    "Tesla", "NVIDIA", "Samsung", "Toyota", "Unilever"
]
selected_companies = st.multiselect(
    "Pilih satu atau lebih perusahaan dari daftar:",
    options=predefined_companies
)

st.markdown("<p style='text-align: center; margin-top: 1em;'>Atau</p>", unsafe_allow_html=True)

manual_input = st.text_area(
    "Masukkan nama perusahaan secara manual (pisahkan dengan koma)",
    placeholder="Contoh: Netflix, Disney, Warner Bros Discovery"
)

if st.button("🚀 Lakukan Analisis Pasar", type="primary"):
    final_companies = sorted(list(set(selected_companies + [c.strip() for c in manual_input.split(',') if c.strip()])))

    # Validasi input
    if not all([langflow_base_url, langflow_flow_id, langflow_bearer]):
        st.warning("Harap lengkapi URL Dasar, ID Flow, dan Bearer Token di sidebar.")
    elif not final_companies:
        st.warning("Harap pilih atau masukkan setidaknya satu nama perusahaan.")
    else:
        st.write(f"**Perusahaan yang akan dianalisis:** {', '.join(final_companies)}")
        with st.spinner("AI sedang melakukan riset pasar... Ini bisa memakan waktu beberapa saat."):
            result = run_langflow_analysis(langflow_base_url, langflow_flow_id, langflow_bearer, final_companies, openai_api_key)
            
            if result:
                st.subheader("✅ Hasil Analisis Riset Pasar")
                st.markdown(result)
            else:
                st.error("Gagal mendapatkan hasil analisis. Mohon periksa kembali konfigurasi di sidebar dan pastikan flow di Langflow berfungsi.")
