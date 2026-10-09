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


# Inicijalizacija stanja
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
        "Unos ulova ručno (Žrijeb/Sektori)",
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
        })
        snimi_podatke()
        st.success(f"Uspješno dodan: {ime_prezime} ({klub_grad})")

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
        st.success("Takmičar i njegovi rezultati su uspješno obrisani!")
        st.rerun()

# ----------------- 2. RUČNI UNOS ULOVA -----------------
elif menu == "Unos ulova ručno (Žrijeb/Sektori)":
  st.subheader("Evidencija ulova po kolama")

  if not st.session_state.takmicari:
    st.info("Prvo unesite takmičare u meniju 'Unos takmičara'.")
  else:
    opcije_takmicara = {
        f"{t['ime']} ({t['klub']})": t["id"] for t in st.session_state.takmicari
    }

    with st.form("form_ulov"):
      odabrani_str = st.selectbox(
          "Izaberi takmičara iz baze", list(opcije_takmicara.keys())
      )
      kolo = st.selectbox("Izaberi kolo / rundu", [1, 2, 3])

      izvučeni_sektor = st.selectbox(
          "Izvučeni sektor za ovo kolo", ["A", "B", "C"]
      )
      broj_staze_int = st.number_input(
          "Broj staze (npr. 4 za A 04)", min_value=1, max_value=30, value=1
      )
      oznaka_staze = f"{izvučeni_sektor} {broj_staze_int:02d}"

      st.info(f"Oznaka staze: **{oznaka_staze}**")

      naziv_staze = st.text_input("Mjesto / Staza", value="DRINA, GORAŽDE")
      datum_kola = st.text_input("Datum kola", value="26.09.2026")

      t_id = opcije_takmicara[odabrani_str]
      trenutni_t = next(t for t in st.session_state.takmicari if t["id"] == t_id)

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
            f"Uspješno snimljeno za {trenutni_t['ime']} ({kolo}. kolo)!"
        )

# ----------------- 3. KAMERA -----------------
elif menu == "📸 Skeniraj listu kamerom":
  st.subheader("📸 Skeniranje sudijske liste putem kamere")
  slika_liste = st.camera_input("Uslikaj sudijsku listu")

  if slika_liste is not None:
    st.success("Slika je uspješno uslikana i sačuvana!")
    st.image(
        slika_liste, caption="Uslikana sudijska lista", use_container_width=True
    )
    with open("poslednja_lista.jpg", "wb") as f:
      f.write(slika_liste.getbuffer())

# ----------------- 4. SLUŽBENI GENERALNI PLASMAN (OPTIMIZOVANO ZA MOBITELE) -----------------
elif menu == "Službeni generalni plasman":
  st.markdown(
      """
        <div style="text-align: center; border-bottom: 2px solid #333; padding-bottom: 10px; margin-bottom: 15px;">
            <h4 style="margin:0;">PRVENSTVO SRS F BIH U MUŠIČARENJU</h4>
            <h3 style="margin:5px 0;">GENERALNI POJEDINAČNI PLASMAN</h3>
            <p style="margin:0; font-size: 14px; font-weight: bold;">Zaključno sa: 3. Kolom</p>
        </div>
        """,
      unsafe_allow_html=True,
  )

  if not st.session_state.takmicari:
    st.info("Nema unesenih podataka.")
  else:
    # Uputstvo za štampu na mobitelu
    st.info(
        "💡 **Savjet za mobitel:** Za printanje ili snimanje u PDF, pritisnite"
        " meni vašeg pretraživača (tri tačkice gore desno) i izaberite opciju"
        " **"
        "Dijeli (Share)"** ili **"Print"**."
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

      rezultati_za_sort.append({
          "id": t["id"],
          "ime": t["ime"],
          "klub": t["klub"],
          "uk_riba": uk_riba,
          "uk_duzina": uk_duzina,
          "uk_poeni": uk_poeni,
          "zbir_plasmana": zbir_plasmana,
          "ulovi": t_ulovi,
      })

    rezultati_za_sort.sort(
        key=lambda x: (x["zbir_plasmana"], -x["uk_riba"], -x["uk_poeni"])
    )

    # Prikaz preko čistih, preglednih kartica i tabela prilagođenih za telefone
    for poz, r in enumerate(rezultati_za_sort, 1):
      with st.container(border=True):
        st.markdown(
            f"**{poz}. {r['ime'].upper()}** — *{r['klub'].upper()}*"
        )

        if r["ulovi"]:
          # Pripremamo podatke za čistu Streamlit tabelu koja se savršeno prilagođava ekranu mobitela
          tabela_podaci = []
          for u in r["ulovi"]:
            tabela_podaci.append({
                "Kolo": u["kolo"],
                "Staza": u["staza"],
                "Sekt/St": u["sektor_staza"],
                "Riba": u["riba"],
                "Dužina(mm)": f"{u['duzina']:.1f}",
                "Poeni": f"{u['poeni']:.1f}",
                "S.Pl.": f"{u['plasman']:.1f}",
            })

          df_prikaz = pd.DataFrame(tabela_podaci)
          st.dataframe(df_prikaz, use_container_width=True, hide_index=True)

          # Ukupne vrijednosti ispod tabele
          st.markdown(
              f"👉 **UKUPNO:** Riba: **{r['uk_riba']}** | Dužina:"
              f" **{r['uk_duzina']:.1f} mm** | Poeni:"
              f" **{r['uk_poeni']:.1f}** | **Zbir plasmana: {r['zbir_plasmana']:.1f}**"
          )
        else:
          st.markdown(
              "_Nema unesenih ulova za ovog takmičara._",
              help="Nema ulova",
          )