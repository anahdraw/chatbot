import streamlit as st
import requests
import json

# --- KONFIGURASI HARDCODE ---
# URL dasar dari aplikasi Langflow Anda di DataStax.
# Ganti dengan URL Anda jika suatu saat berubah.
LANGFLOW_BASE_URL = "https://api.langflow.astra.datastax.com/lf/115811d4-1b67-443e-b29a-5db8ec947ec6/api/v1/run/5f371299-11e3-4175-b4ec-c980576bfd6b"

# Fungsi untuk memanggil endpoint Langflow
def run_langflow_analysis(flow_id, bearer_token, company_names, openai_api_key=None):
    """
    Mengirim permintaan ke endpoint Langflow dengan URL dasar yang sudah ditentukan di dalam kode.
    """
    # Membangun URL API dari URL dasar yang di-hardcode dan Flow ID dari input pengguna
    api_endpoint = f"{LANGFLOW_BASE_URL.rstrip('/')}/api/v1/run/{flow_id}"

    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json"
    }
    
    # Payload yang dikirim ke Langflow. Sesuaikan 'input_value' jika perlu.
    payload = {
        "input_value": f"Lakukan riset pasar mendalam untuk perusahaan-perusahaan berikut: {', '.join(company_names)}. Berikan analisis tentang posisi pasar, kompetitor utama, kekuatan, kelemahan, dan potensi pertumbuhan mereka.",
        "output_type": "chat",
        "input_type": "chat",
        "tweaks": {
            # Anda bisa menambahkan tweak di sini jika flow Anda membutuhkannya
            # Contoh: "OpenAI-XXXXX": {"openai_api_key": openai_api_key}
        }
    }

    st.info(f"Mengirim permintaan ke Langflow...")
    # Untuk debugging, Anda bisa menghapus komentar di baris berikut untuk melihat URL lengkapnya
    # st.code(f"Endpoint URL: {api_endpoint}")

    try:
        response = requests.post(api_endpoint, headers=headers, data=json.dumps(payload), timeout=300)
        response.raise_for_status()
        
        result = response.json()
        
        # Ekstrak pesan dari output. Jalur ini mungkin perlu disesuaikan dengan struktur flow Anda.
        final_text = result.get("outputs", [{}])[0].get("outputs", [{}])[0].get("results", {}).get("message", {}).get("data", {}).get("text", "")
        
        if not final_text:
             st.warning("Berhasil terhubung, namun tidak ada teks yang bisa diekstrak dari respons. Silakan periksa struktur output flow Anda di Langflow.")
             st.write("Struktur Respons Mentah dari Langflow:")
             st.json(result)

        return final_text

    except requests.exceptions.HTTPError as http_err:
        st.error(f"HTTP Error terjadi: {http_err}")
        st.error(f"Pastikan Flow ID dan Bearer Token Anda sudah benar. Response: {http_err.response.text}")
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
    st.header("⚙️ Konfigurasi Wajib")
    langflow_flow_id = st.text_input(
        "Langflow Flow ID",
        placeholder="Masukkan ID unik dari flow Anda",
        help="Salin ID unik dari flow yang ingin Anda gunakan dari URL Langflow."
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
    # Menggabungkan dan membersihkan daftar perusahaan
    manual_list = [c.strip() for c in manual_input.split(',') if c.strip()]
    final_companies = sorted(list(set(selected_companies + manual_list)))

    # Validasi input
    if not all([langflow_flow_id, langflow_bearer]):
        st.warning("Harap lengkapi Flow ID dan Bearer Token di sidebar.")
    elif not final_companies:
        st.warning("Harap pilih atau masukkan setidaknya satu nama perusahaan.")
    else:
        st.write(f"**Perusahaan yang akan dianalisis:** {', '.join(final_companies)}")
        with st.spinner("AI sedang melakukan riset pasar... Ini bisa memakan waktu beberapa saat."):
            result = run_langflow_analysis(langflow_flow_id, langflow_bearer, final_companies, openai_api_key)
            
            if result:
                st.subheader("✅ Hasil Analisis Riset Pasar")
                st.markdown(result)
            else:
                st.error("Gagal mendapatkan hasil analisis. Mohon periksa kembali konfigurasi di sidebar dan pastikan flow di Langflow berfungsi.")
