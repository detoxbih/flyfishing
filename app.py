import pandas as pd
import streamlit as st

# Podešavanje stranice
st.set_page_config(
    page_title="Una Fly - Takmičenje", page_icon="🎣", layout="wide"
)

# --- 1. BOČNA TRAKA (SIDEBAR) SA LOGOTIPOM ---
st.sidebar.header("Administracija takmičenja")

# Automatski učitava grb kluba ako je fajl tu
try:
  st.sidebar.image("logo.jpg", use_container_width=True)
except Exception:
  try:
    st.sidebar.image("logo.png", use_container_width=True)
  except Exception:
    pass  # Ako slika nije pronađena, aplikacija normalno nastavlja rad

menu = st.sidebar.selectbox(
    "Izaberite opciju",
    [
        "Unos takmičara",
        "Unos ulova po rundama",
        "Pregled rang-liste i sektora",
    ],
)

# Glavni naslov aplikacije
st.title("🎣 Una Fly - Fly Fishing Takmičenje")
st.markdown("### Bodovanje po sektorima i rotacijama (3 runde)")

# Inicijalizacija memorije u sesiji
if "takmicari" not in st.session_state:
  st.session_state.takmicari = []

if "ulovi" not in st.session_state:
  st.session_state.ulovi = []

if menu == "Unos takmičara":
  st.subheader("Registracija takmičara i početnog sektora")
  st.info(
      "Sistem automatski rotira takmičare: Runda 1 (Početni sektor),"
      " Runda 2 (Sljedeći sektor), Runda 3 (Zadnji sektor)."
  )

  with st.form("form_takmicar"):
    ime_prezime = st.text_input("Ime i prezime takmičara")
    pocetni_sektor = st.selectbox("Početni sektor (Runda 1)", ["A", "B", "C"])
    submit_t = st.form_submit_button("Dodaj takmičara")

    if submit_t:
      if ime_prezime.strip() == "":
        st.warning("Molimo unesite ime i prezime.")
      else:
        novi_id = len(st.session_state.takmicari) + 1
        st.session_state.takmicari.append({
            "id": novi_id,
            "ime": ime_prezime,
            "pocetni_sektor": pocetni_sektor,
        })
        st.success(
            f"Uspješno dodan: {ime_prezime} (Početak u Sektoru"
            f" {pocetni_sektor})"
        )

  if st.session_state.takmicari:
    st.write("---")
    st.write("### Trenutno prijavljeni takmičari:")
    df_t = pd.DataFrame(st.session_state.takmicari)
    st.dataframe(
        df_t[["id", "ime", "pocetni_sektor"]].rename(
            columns={
                "id": "ID",
                "ime": "Ime i prezime",
                "pocetni_sektor": "Početni sektor",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )

elif menu == "Unos ulova po rundama":
  st.subheader("Evidencija ulova po rundama (60 minuta)")

  if not st.session_state.takmicari:
    st.info("Prvo unesite takmičare kroz opciju 'Unos takmičara'.")
  else:

    def izracunaj_sektor(pocetni, runda):
      sektori = ["A", "B", "C"]
      idx = sektori.index(pocetni)
      return sektori[(idx + runda - 1) % 3]

    opcije_takmicara = {
        f"{t['ime']} (Start u Sektoru {t['pocetni_sektor']})": t["id"]
        for t in st.session_state.takmicari
    }

    with st.form("form_ulov"):
      odabrani_str = st.selectbox(
          "Izaberi takmičara", list(opcije_takmicara.keys())
      )
      runda = st.selectbox(
          "Izaberi rundu", [1, 2, 3], format_func=lambda x: f"Runda {x} (60 min)"
      )

      t_id = opcije_takmicara[odabrani_str]
      trenutni_t = next(t for t in st.session_state.takmicari if t["id"] == t_id)
      aktuelni_sektor = izracunaj_sektor(trenutni_t["pocetni_sektor"], runda)

      st.markdown(
          f"ℹ️ U **rundici {runda}**, ovaj takmičar peca u **Sektoru"
          f" {aktuelni_sektor}**."
      )

      broj_riba = st.number_input(
          "Broj upecanih riba (komada)", min_value=0, step=1, value=0
      )
      ukupna_duzina = st.number_input(
          "Ukupna dužina riba u toj rundi (cm)",
          min_value=0.0,
          step=0.5,
          format="%.1f",
      )

      submit_u = st.form_submit_button("Snimi ulov za ovu rundu")

      if submit_u:
        bodovi = (broj_riba * 100) + (ukupna_duzina * 10)
        postojeci = next(
            (
                u
                for u in st.session_state.ulovi
                if u["takmicar_id"] == t_id and u["runda"] == runda
            ),
            None,
        )

        if postojeci:
          postojeci["riba"] = broj_riba
          postojeci["duzina"] = ukupna_duzina
          postojeci["bodovi"] = bodovi
        else:
          st.session_state.ulovi.append({
              "takmicar_id": t_id,
              "runda": runda,
              "sektor": aktuelni_sektor,
              "riba": broj_riba,
              "duzina": ukupna_duzina,
              "bodovi": bodovi,
          })

        st.success(
            f"Ulov uspješno snimljen za {trenutni_t['ime']} (Runda {runda} -"
            f" Sektor {aktuelni_sektor})!"
        )

elif menu == "Pregled rang-liste i sektora":
  st.subheader("📊 Rang-liste i rezultati po rundama")

  if not st.session_state.takmicari:
    st.info("Nema podataka za prikaz.")
  else:
    rezultati = []
    for t in st.session_state.takmicari:
      t_ulovi = [
          u for u in st.session_state.ulovi if u["takmicar_id"] == t["id"]
      ]
      ukupno_riba = sum(u["riba"] for u in t_ulovi)
      ukupno_cm = sum(u["duzina"] for u in t_ulovi)
      ukupno_bodova = sum(u["bodovi"] for u in t_ulovi)

      rezultati.append({
          "ime": t["ime"],
          "pocetni_sektor": t["pocetni_sektor"],
          "riba": ukupno_riba,
          "duzina": ukupno_cm,
          "bodovi": ukupno_bodova,
      })

    df_res = pd.DataFrame(rezultati)

    st.markdown("### 🏆 Ukupna generalna lista takmičenja")
    df_gen = df_res.sort_values(
        by=["bodovi", "duzina"], ascending=[False, False]
    ).reset_index(drop=True)
    df_gen.index = df_gen.index + 1

    df_gen_prikaz = df_gen[
        ["ime", "pocetni_sektor", "riba", "duzina", "bodovi"]
    ].rename(
        columns={
            "ime": "Ime i prezime",
            "pocetni_sektor": "Pošt. Sektor",
            "riba": "Ukupno riba",
            "duzina": "Ukupno cm",
            "bodovi": "Ukupno bodova",
        }
    )
    st.dataframe(df_gen_prikaz, use_container_width=True)

    if st.session_state.ulovi:
      st.markdown("---")
      st.markdown("### 📋 Svi uneseni ulovi po rundama")
      df_ulovi_raw = pd.DataFrame(st.session_state.ulovi)
      mapa_imena = {t["id"]: t["ime"] for t in st.session_state.takmicari}
      df_ulovi_raw["Ime i prezime"] = df_ulovi_raw["takmicar_id"].map(
          mapa_imena
      )

      df_ulovi_prikaz = df_ulovi_raw[
          ["Ime i prezime", "runda", "sektor", "riba", "duzina", "bodovi"]
      ].rename(
          columns={
              "runda": "Runda",
              "sektor": "Sektor u rundi",
              "riba": "Riba",
              "duzina": "Dužina (cm)",
              "bodovi": "Bodovi",
          }
      )
      st.dataframe(
          df_ulovi_prikaz.sort_values(by=["Runda", "Sektor u rundi"]),
          use_container_width=True,
          hide_index=True,
      )