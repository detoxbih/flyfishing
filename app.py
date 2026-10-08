import json
import os
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Una Fly - Službeni Plasman", page_icon="🎣", layout="wide"
)

FAJL_BAZE = "baza_takmicenja.json"


def ucitaj_podatke():
  if os.path.exists(FAJL_BAZE):
    try:
      with open(FAJL_BAZE, "r", encoding="utf-8") as f:
        return json.load(f)
    except Exception:
      pass
  return {"takmicari": [], "ulovi": []}


def snimi_podatke():
  podaci = {
      "takmicari": st.session_state.takmicari,
      "ulovi": st.session_state.ulovi,
  }
  with open(FAJL_BAZE, "w", encoding="utf-8") as f:
    json.dump(podaci, f, ensure_ascii=False, indent=4)


# Inicijalizacija stanje i učitavanje iz fajla
if "podaci_ucitani" not in st.session_state:
  saved = ucitaj_podatke()
  st.session_state.takmicari = saved.get("takmicari", [])
  st.session_state.ulovi = saved.get("ulovi", [])
  st.session_state.podaci_ucitani = True

if "takmicari" not in st.session_state:
  st.session_state.takmicari = []
if "ulovi" not in st.session_state:
  st.session_state.ulovi = []

st.sidebar.header("Administracija takmičenja")

try:
  st.sidebar.image("logo.jpg", use_container_width=True)
except Exception:
  try:
    st.sidebar.image("logo.png", use_container_width=True)
  except Exception:
    pass

menu = st.sidebar.selectbox(
    "Izaberite opciju",
    [
        "Unos takmičara",
        "Unos ulova ručno",
        "📸 Skeniraj listu kamerom",
        "Službeni generalni plasman",
    ],
)

st.sidebar.markdown("---")
if st.sidebar.button("💾 Sačuvaj sve podatke"):
  snimi_podatke()
  st.sidebar.success("Podaci su uspješno sačuvani u fajl!")

if st.sidebar.button("🔄 Resetuj / Obriši sve podatke"):
  st.session_state.takmicari = []
  st.session_state.ulovi = []
  if os.path.exists(FAJL_BAZE):
    os.remove(FAJL_BAZE)
  st.sidebar.success("Baza je očišćena!")
  st.rerun()

# ----------------- 1. UNOS I BRISANJE TAKMIČARA -----------------
if menu == "Unos takmičara":
  st.subheader("Registracija i upravljanje takmičarima")

  with st.form("form_takmicar"):
    st.write("### Dodaj novog takmičara")
    ime_prezime = st.text_input("Ime i prezime takmičara")
    klub_grad = st.text_input("Klub / Država (npr. BOSANSKA KRUPA)")
    pocetni_sektor = st.selectbox(
        "Početni sektor (Sektor u 1. kolu)", ["A", "B", "C"]
    )
    submit_t = st.form_submit_button("Dodaj takmičara")

    if submit_t:
      if ime_prezime.strip() == "":
        st.warning("Molimo unesite ime i prezime.")
      else:
        novi_id = (
            max([t["id"] for t in st.session_state.takmicari], default=0) + 1
        )
        st.session_state.takmicari.append({
            "id": novi_id,
            "ime": ime_prezime,
            "klub": klub_grad,
            "pocetni_sektor": pocetni_sektor,
        })
        snimi_podatke()
        st.success(
            f"Uspješno dodan: {ime_prezime} ({klub_grad}) sa početnim sektorom"
            f" {pocetni_sektor}"
        )

  if st.session_state.takmicari:
    st.write("---")
    st.write("### Prijavljeni takmičari u bazi:")
    df_t = pd.DataFrame(st.session_state.takmicari)
    st.dataframe(df_t, use_container_width=True, hide_index=True)

    st.write("### ❌ Brisanje takmičara (u slučaju greške)")
    opcije_za_brisanje = {
        f"{t['ime']} ({t['klub']}) [ID: {t['id']}]": t["id"]
        for t in st.session_state.takmicari
    }

    with st.form("form_brisanje"):
      odabrani_za_bris = st.selectbox(
          "Izaberi takmičara za brisanje", list(opcije_za_brisanje.keys())
      )
      submit_b = st.form_submit_button(
          "🗑️ Obriši izabranog takmičara i njegove ulove"
      )

      if submit_b:
        id_za_brisanje = opcije_za_brisanje[odabrani_za_bris]
        st.session_state.takmicari = [
            t for t in st.session_state.takmicari if t["id"] != id_za_brisanje
        ]
        st.session_state.ulovi = [
            u for u in st.session_state.ulovi if u["takmicar_id"] != id_za_brisanje
        ]
        snimi_podatke()
        st.success(
            f"Takmičar i njegovi rezultati su uspješno obrisani iz baze!"
        )
        st.rerun()

# ----------------- 2. RUČNI UNOS ULOVA -----------------
elif menu == "Unos ulova ručno":
  st.subheader("Evidencija ulova po kolama (Sektori se automatski rotiraju)")

  if not st.session_state.takmicari:
    st.info("Prvo unesite takmičare u meniju 'Unos takmičara'.")
  else:

    def izracunaj_sektor(pocetni, runda):
      sektori = ["A", "B", "C"]
      idx = sektori.index(pocetni)
      return sektori[(idx + runda - 1) % 3]

    opcije_takmicara = {
        f"{t['ime']} ({t['klub']}) [Start: {t['pocetni_sektor']}]": t["id"]
        for t in st.session_state.takmicari
    }

    with st.form("form_ulov"):
      odabrani_str = st.selectbox(
          "Izaberi takmičara iz baze", list(opcije_takmicara.keys())
      )
      kolo = st.selectbox("Izaberi kolo / rundu", [1, 2, 3])

      col1, col2 = st.columns(2)
      with col1:
        naziv_staze = st.text_input("Mjesto / Staza", value="DRINA, GORAŽDE")
      with col2:
        datum_kola = st.text_input("Datum kola", value="26.09.2026")

      t_id = opcije_takmicara[odabrani_str]
      trenutni_t = next(t for t in st.session_state.takmicari if t["id"] == t_id)

      aktuelni_sektor = izracunaj_sektor(trenutni_t["pocetni_sektor"], kolo)

      broj_staze_int = st.number_input(
          "Broj staze (npr. 3 za A 03)", min_value=1, max_value=30, value=1
      )
      oznaka_staze = f"{aktuelni_sektor} {broj_staze_int:02d}"

      st.info(
          f"ℹ️ Za {kolo}. kolo takmičar **{trenutni_t['ime']}** automatski peca"
          f" u sektoru: **{aktuelni_sektor}** (Staza: {oznaka_staze})"
      )

      broj_riba = st.number_input("Broj riba", min_value=0, step=1, value=0)
      duzina_mm = st.number_input(
          "Ukupna dužina u mm", min_value=0.0, step=1.0, value=0.0
      )
      plasman_sektor = st.number_input(
          "Sektorski plasman (S.pl.)", min_value=1.0, step=1.0, value=1.0
      )

      submit_u = st.form_submit_button("Snimi rezultate kola")

      if submit_u:
        poeni = (broj_riba * 100) + duzina_mm

        postojeci = next(
            (
                u
                for u in st.session_state.ulovi
                if u["takmicar_id"] == t_id and u["kolo"] == kolo
            ),
            None,
        )

        novi_podatak_kola = {
            "takmicar_id": t_id,
            "kolo": kolo,
            "staza": naziv_staze,
            "datum": datum_kola,
            "sektor_staza": oznaka_staze,
            "riba": int(broj_riba),
            "duzina": float(duzina_mm),
            "poeni": float(poeni),
            "plasman": float(plasman_sektor),
        }

        if postojeci:
          postojeci.update(novi_podatak_kola)
        else:
          st.session_state.ulovi.append(novi_podatak_kola)

        snimi_podatke()
        st.success(
            f"Uspješno snimljeno za {trenutni_t['ime']} ({kolo}. kolo, Sektor"
            f" {aktuelni_sektor})!"
        )

# ----------------- 3. KAMERA -----------------
elif menu == "📸 Skeniraj listu kamerom":
  st.subheader("📸 Skeniranje sudijske liste putem kamere")
  st.info("Uslikajte popunjenu sudijsku listu radi arhive i provjere.")

  slika_liste = st.camera_input("Uslikaj sudijsku listu")

  if slika_liste is not None:
    st.success("Slika je uspješno uslikana i sačuvana!")
    st.image(
        slika_liste, caption="Uslikana sudijska lista", use_container_width=True
    )

    with open("poslednja_lista.jpg", "wb") as f:
      f.write(slika_liste.getbuffer())
    st.write("ℹ️ Slika je zabilježena u sistemu.")

# ----------------- 4. SLUŽBENI GENERALNI PLASMAN -----------------
elif menu == "Službeni generalni plasman":
  st.markdown(
      """
        <div style="text-align: center; border-bottom: 2px solid black; padding-bottom: 10px; margin-bottom: 20px;">
            <h3 style="margin:0; font-family:serif;">PRVENSTVO SRS F BIH U MUŠIČARENJU</h3>
            <h2 style="margin:5px 0; font-family:serif;">GENERALNI POJEDINAČNI PLASMAN U FLY FISHING-U : - SENIORI</h2>
            <p style="margin:0; font-weight: bold;">Zakljucno sa : 3. Kolom</p>
        </div>
        """,
      unsafe_allow_html=True,
  )

  if not st.session_state.takmicari:
    st.info("Nema unesenih podataka.")
  else:
    st.markdown(
        """
          <div style="text-align: right; margin-bottom: 15px;">
              <button onclick="window.print()" style="background-color:#2c3e50; color:white; padding:8px 16px; border:none; border-radius:4px; cursor:pointer; font-size:14px; font-weight:bold;">
                  🖨️ Isprintaj / Sačuvaj kao PDF
              </button>
          </div>
          """,
        unsafe_allow_html=True,
    )

    rezultati_za_sort = []
    for t in st.session_state.takmicari:
      t_ulovi = [
          u for u in st.session_state.ulovi if u["takmicar_id"] == t["id"]
      ]
      t_ulovi.sort(key=lambda x: x["kolo"])

      uk_riba = sum(u["riba"] for u in t_ulovi)
      uk_duzina = sum(u["duzina"] for u in t_ulovi)
      uk_poeni = sum(u["poeni"] for u in t_ulovi)
      zbir_plasmana = sum(u["plasman"] for u in t_ulovi)

      rezultati_za_sort.