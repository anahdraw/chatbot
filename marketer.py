import streamlit as st
import requests
import json

# Fungsi untuk memanggil endpoint Langflow
def run_langflow_analysis(langflow_url, bearer_token, company_names, openai_api_key=None):
    """
    Mengirim permintaan ke endpoint Langflow untuk analisis riset pasar.
    """
    # Pastikan URL diakhiri dengan '/run'
    # Sesuaikan 'chat' jika nama input di flow Anda berbeda
    api_endpoint = f"{langflow_url.rstrip('/')}/run"
    
    # Header untuk otentikasi
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json"
    }
    
    # Payload yang akan dikirim. Strukturnya harus sesuai dengan flow Anda di Langflow.
    # Biasanya, flow memiliki input_value, dan Anda bisa mengirim variabel lain di 'tweaks'.
    # Ganti 'ChatInput-XXXXX' dengan ID komponen input di flow Langflow Anda.
    # Anda bisa menemukan ID ini dengan mengekspor flow Anda dan melihat file JSON-nya.
    payload = {
        "input_value": f"Lakukan riset pasar untuk perusahaan berikut: {', '.join(company_names)}",
        "output_type": "chat", # Atau 'text' tergantung tipe output Anda
        "input_type": "chat",  # Atau 'text' tergantung tipe input Anda
        "tweaks": {
            # Contoh: Jika Anda punya komponen OpenAI di flow yang butuh API key
            # "OpenAI-XXXXX": {
            #     "openai_api_key": openai_api_key
            # }
        }
    }

    st.info(f"Mengirim permintaan ke: {api_endpoint}")
    st.json(payload) # Menampilkan payload untuk debugging

    try:
        response = requests.post(api_endpoint, headers=headers, data=json.dumps(payload), stream=True, timeout=300)
        response.raise_for_status()  # Akan memunculkan error jika status code bukan 2xx

        # Memproses response streaming dari Langflow
        full_response = ""
        for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
            try:
                # Setiap chunk bisa jadi JSON object terpisah
                data = json.loads(chunk.strip())
                # Ekstrak pesan dari output. Strukturnya mungkin berbeda, sesuaikan!
                # Misalnya, bisa di dalam data['outputs'][0]['outputs'][0]['results']['message']['data']['text']
                # Gunakan st.write(data) untuk inspeksi struktur respons saat pertama kali mencoba
                message_content = data.get("outputs", [{}])[0].get("outputs", [{}])[0].get("results", {}).get("message", {}).get("data", {}).get("text", "")
                if message_content:
                    full_response += message_content
                    # Anda bisa membuat efek streaming di sini jika mau
            except json.JSONDecodeError:
                # Kadang ada chunk kosong atau non-JSON, abaikan saja
                continue
                
        if not full_response:
             st.warning("Tidak ada konten yang dapat diekstrak dari respons. Silakan periksa struktur respons Langflow Anda.")
             st.write("Respons mentah yang diterima:", response.text)

        return full_response

    except requests.exceptions.RequestException as e:
        st.error(f"Terjadi kesalahan saat menghubungi API Langflow: {e}")
        st.error(f"Response Body: {e.response.text if e.response else 'No response'}")
        return None

# --- UI Aplikasi Streamlit ---

st.set_page_config(page_title="Market Research AI", layout="wide")

# Judul Utama
st.title("🔬 Market Research Analysis dengan Langflow")
st.markdown("Aplikasi ini menggunakan flow dari Langflow untuk melakukan riset pasar pada perusahaan yang Anda pilih.")

# Sidebar untuk konfigurasi
with st.sidebar:
    st.header("⚙️ Konfigurasi Koneksi")
    langflow_url = st.text_input(
        "URL Endpoint Langflow",
        placeholder="https.yourapp.datastax.com/api/v1/run/your-flow-id",
        help="URL API dari flow yang Anda deploy di Langflow."
    )
    langflow_bearer = st.text_input(
        "Langflow Bearer Token", 
        type="password",
        help="Token API untuk otentikasi dengan Langflow."
    )
    st.markdown("---")
    st.header("Konfigurasi Opsional")
    openai_api_key = st.text_input(
        "OpenAI API Key (jika perlu)", 
        type="password",
        help="Masukkan jika flow Anda di Langflow membutuhkan API key OpenAI secara eksplisit."
    )
    st.info("Konfigurasi ini tidak disimpan dan hanya berlaku untuk sesi ini.")

# Konten utama
st.header("Pilih Perusahaan untuk Dianalisis")

# Opsi 1: Memilih dari daftar
predefined_companies = [
    "Google (Alphabet)", "Microsoft", "Apple", "Amazon", "Meta (Facebook)",
    "Tesla", "NVIDIA", "Samsung", "Toyota", "Unilever"
]
selected_companies = st.multiselect(
    "Pilih satu atau lebih perusahaan dari daftar:",
    options=predefined_companies
)

# Opsi 2: Input manual
st.write("Atau")
manual_input = st.text_area(
    "Masukkan nama perusahaan secara manual (pisahkan dengan koma)",
    placeholder="Contoh: Netflix, Disney, Warner Bros Discovery"
)

# Tombol untuk memulai analisis
if st.button("🚀 Lakukan Analisis Pasar"):
    # Menggabungkan input dari kedua sumber
    final_companies = list(selected_companies)
    if manual_input:
        manual_list = [company.strip() for company in manual_input.split(',')]
        final_companies.extend(manual_list)
    
    # Menghapus duplikat
    final_companies = sorted(list(set(final_companies)))

    # Validasi input
    if not langflow_url or not langflow_bearer:
        st.warning("Harap masukkan URL Endpoint Langflow dan Bearer Token di sidebar.")
    elif not final_companies:
        st.warning("Harap pilih atau masukkan setidaknya satu nama perusahaan.")
    else:
        st.write(f"**Perusahaan yang akan dianalisis:** {', '.join(final_companies)}")
        with st.spinner("AI sedang melakukan riset pasar... Ini mungkin memakan waktu beberapa saat."):
            # Panggil fungsi untuk analisis
            result = run_langflow_analysis(langflow_url, langflow_bearer, final_companies, openai_api_key)
            
            if result:
                st.subheader("✅ Hasil Analisis Riset Pasar")
                st.markdown(result)
            else:
                st.error("Gagal mendapatkan hasil analisis. Mohon periksa konfigurasi dan coba lagi.")
