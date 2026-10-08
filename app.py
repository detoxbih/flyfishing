import json
import os
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Una Fly - Takmičenje", page_icon="🎣", layout="wide"
)

FAJL_BAZE = "baza_takmicenja.json"


def ucitaj_podatke():
  if os.path.exists(FAJL_BAZE):
    with open(FAJL_BAZE, "r", encoding="utf-8") as f:
      return json.load(f)
  return {"takmicari": [], "ulovi": []}


def snimi_podatke():
  podaci = {
      "takmicari": st.session_state.takmicari,
      "ulovi": st.session_state.ulovi,
  }
  with open(FAJL_BAZE, "w", encoding="utf-8") as f:
    json.dump(podaci, f, ensure_ascii=False, indent=4)


if "podaci_ucitani" not in st.session_state:
  saved = ucitaj_podatke()
  st.session_state.takmicari = saved["takmicari"]
  st.session_state.ulovi = saved["ulovi"]
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

if st.sidebar.button("🔄 Resetuj / Obriši sve podatke"):
  st.session_state.takmicari = []
  st.session_state.ulovi = []
  if os.path.exists(FAJL_BAZE):
    os.remove(FAJL_BAZE)
  st.sidebar.success("Baza je očišćena!")
  st.rerun()

st.title("🎣 Una Fly - Službeni izvještaj takmičenja")

if menu == "Unos takmičara":
  st.subheader("Registracija takmičara, kluba/grada i početnog sektora")

  with st.form("form_takmicar"):
    ime_prezime = st.text_input("Ime i prezime takmičara")
    klub_grad = st.text_input("Klub / Grad (npr. BIHAĆ / UNA)")
    pocetni_sektor = st.selectbox("Početni sektor (Kolo 1)", ["A", "B", "C"])
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
        st.success(f"Uspješno dodan: {ime_prezime} ({klub_grad})")

  if st.session_state.takmicari:
    st.write("---")
    st.write("### Prijavljeni takmičari:")
    df_t = pd.DataFrame(st.session_state.takmicari)
    st.dataframe(df_t, use_container_width=True, hide_index=True)

elif menu == "Unos ulova ručno":
  st.subheader("Klasična evidencija ulova po kolama")

  if not st.session_state.takmicari:
    st.info("Prvo unesite takmičare.")
  else:

    def izracunaj_sektor(pocetni, runda):
      sektori = ["A", "B", "C"]
      idx = sektori.index(pocetni)
      return sektori[(idx + runda - 1) % 3]

    opcije_takmicara = {
        f"{t['ime']} ({t['klub']}) - Start: {t['pocetni_sektor']}": t["id"]
        for t in st.session_state.takmicari
    }

    with st.form("form_ulov"):
      odabrani_str = st.selectbox(
          "Izaberi takmičara", list(opcije_takmicara.keys())
      )
      kolo = st.selectbox("Izaberi kolo / rundu", [1, 2, 3])
      naziv_staze = st.text_input(
          "Naziv staze / Vode (npr. UNA, BIHAĆ)", value="UNA, BIHAĆ"
      )

      t_id = opcije_takmicara[odabrani_str]
      trenutni_t = next(t for t in st.session_state.takmicari if t["id"] == t_id)
      aktuelni_sektor = izracunaj_sektor(trenutni_t["pocetni_sektor"], kolo)

      st.info(
          f"U {kolo}. kolu ovaj takmičar peca u Sektoru **{aktuelni_sektor}**."
      )

      broj_riba = st.number_input("Broj riba", min_value=0, step=1, value=0)
      duzina_mm = st.number_input(
          "Ukupna dužina u mm", min_value=0.0, step=1.0, value=0.0
      )
      plasman_sektor = st.number_input(
          "Plasman u sektoru (npr. 1.0, 2.0...)",
          min_value=1.0,
          step=1.0,
          value=1.0,
      )

      submit_u = st.form_submit_button("Snimi rezultate kola")

      if submit_u:
        bodovi_formula = (broj_riba * 100) + (duzina_mm / 10 * 10)

        postojeci = next(
            (
                u
                for u in st.session_state.ulovi
                if u["takmicar_id"] == t_id and u["kolo"] == kolo
            ),
            None,
        )

        if postojeci:
          postojeci["staza"] = naziv_staze
          postojeci["sektor"] = aktuelni_sektor
          postojeci["riba"] = broj_riba
          postojeci["duzina"] = duzina_mm
          postojeci["plasman"] = plasman_sektor
          postojeci["bodovi"] = bodovi_formula
        else:
          st.session_state.ulovi.append({
              "takmicar_id": t_id,
              "kolo": kolo,
              "staza": naziv_staze,
              "sektor": aktuelni_sektor,
              "riba": broj_riba,
              "duzina": duzina_mm,
              "plasman": plasman_sektor,
              "bodovi": bodovi_formula,
          })

        snimi_podatke()
        st.success(
            f"Uspješno snimljeno za {trenutni_t['ime']} ({kolo}. kolo)!"
        )

elif menu == "📸 Skeniraj listu kamerom":
  st.subheader("📸 Skeniranje sudijske liste putem kamere")
  st.info(
      "Uslikajte popunjenu sudijsku listu na kraju runde radi arhive i"
      " provjere."
  )

  slika_liste = st.camera_input("Uslikaj sudijsku listu")

  if slika_liste is not None:
    st.success("Slika je uspješno uslikana i sačuvana!")
    st.image(
        slika_liste, caption="Uslikana sudijska lista", use_container_width=True
    )

    with open("poslednja_lista.jpg", "wb") as f:
      f.write(slika_liste.getbuffer())
    st.write("ℹ️ Slika je zabilježena u sistemu.")

elif menu == "Službeni generalni plasman":
  st.subheader(
      "🏆 PRVENSTVO U MUŠIČARENJU - GENERALNI POJEDINAČNI PLASMAN (SLUŽBENA"
      " LISTA)"
  )

  if not st.session_state.takmicari:
    st.info("Nema unesenih podataka.")
  else:
    st.markdown(
        """
        <button onclick="window.print()" style="background-color:#4CAF50; color:white; padding:10px 20px; border:none; border-radius:5px; cursor:pointer; font-size:16px; font-weight:bold; margin-bottom:20px;">
            🖨️ Isprintaj / Sačuvaj kao PDF
        </button>
        """,
        unsafe_allow_html=True,
    )

    rezultati_za_sort = []
    for t in st.session_state.takmicari:
      t_ulovi = [
          u for u in st.session_state.ulovi if u["takmicar_id"] == t["id"]
      ]
      uk_riba = sum(u["riba"] for u in t_ulovi)
      uk_duzina = sum(u["duzina"] for u in t_ulovi)
      uk_bodovi = sum(u["bodovi"] for u in t_ulovi)
      zbir_plasmana = sum(u["plasman"] for u in t_ulovi)

      rezultati_za_sort.append({
          "id": t["id"],
          "ime": t["ime"],
          "klub": t["klub"],
          "uk_riba": uk_riba,
          "uk_duzina": uk_duzina,
          "uk_bodovi": uk_bodovi,
          "zbir_plasmana": zbir_plasmana,
          "ulovi": t_ulovi,
      })

    rezultati_za_sort.sort(
        key=lambda x: (x["zbir_plasmana"], -x["uk_riba"], -x["uk_duzina"])
    )

    for poz, r in enumerate(rezultati_za_sort, 1):
      st.markdown(
          f"**{poz}. {r['ime'].upper()}** &nbsp;&nbsp;|&nbsp;&nbsp;"
          f" *{r['klub'].upper()}*"
      )

      if r["ulovi"]:
        df_kola = pd.DataFrame(r["ulovi"])
        df_kola_prikaz = df_kola[
            ["staza", "sektor", "riba", "duzina", "plasman"]
        ].rename(
            columns={
                "staza": "Mjesto / Staza",
                "sektor": "Sekt.",
                "riba": "Br. riba",
                "duzina": "Dužina (mm)",
                "plasman": "Plasman",
            }
        )
        st.dataframe(df_kola_prikaz, use_container_width=True, hide_index=True)
        st.markdown(
            f"👉 **UKUPNO:** Riba: **{r['uk_riba']}** | Dužina: **{r['uk_duzina']}"
            f" mm** | **Zbir plasmana: {r['zbir_plasmana']}**"
        )
      else:
        st.write("Nema unesenih ulova za kola.")
      st.markdown("---")