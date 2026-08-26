import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker
import datetime
import time

# ==========================================
# 1. DATABASE SETUP
# ==========================================
Base = declarative_base()

class Team(Base):
    __tablename__ = 'teams'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    is_our_team = Column(Integer, default=0)

class Player(Base):
    __tablename__ = 'players'
    id = Column(Integer, primary_key=True)
    team_id = Column(Integer, ForeignKey('teams.id'))
    number = Column(Integer, nullable=False)
    surname = Column(String, nullable=False)
    role = Column(String, default="Schiacciatrice")

class ScoutEvent(Base):
    __tablename__ = 'scout_events'
    id = Column(Integer, primary_key=True)
    match_id = Column(Integer, default=1)
    player_number = Column(Integer)
    player_surname = Column(String)
    skill = Column(String)
    evaluation = Column(String)
    target_zone = Column(Integer)
    match_time = Column(String)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

class SubstitutionEvent(Base):
    __tablename__ = 'substitutions'
    id = Column(Integer, primary_key=True)
    match_id = Column(Integer, default=1)
    player_out_num = Column(Integer)
    player_out_name = Column(String)
    player_in_num = Column(Integer)
    player_in_name = Column(String)
    match_time = Column(String)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

engine = create_engine('sqlite:///volley_scout_pro_v7.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
db = Session()

# Popolamento iniziale
default_team = db.query(Team).filter_by(name="LIBERTAS SANPAOLO").first()
if not default_team:
    default_team = Team(name="LIBERTAS SANPAOLO", is_our_team=1)
    db.add(default_team)
    db.commit()

    players_data = [
        (7, "ERRICO", "S"), (12, "CIVARDI", "P"), (9, "VERDI", "C"), 
        (4, "GILIO", "L"), (15, "CORNIA", "C"), (10, "GORRA", "S"),
        (6, "DICINTIO", "S"), (3, "CAPRA", "C"), (17, "CARINI", "O"),
        (18, "ANDRONI", "S"), (11, "PIGHI", "L"), (16, "GENZIANELLA", "C"), (21, "GIOVANNACCI", "C")
    ]
    for num, sur, role in players_data:
        db.add(Player(team_id=default_team.id, number=num, surname=sur, role=role))
    db.commit()

existing_opps = db.query(Team).filter_by(is_our_team=0).all()
if not existing_opps:
    for op_name in ["OLYMPIA ROMA", "PRO PATRIA", "IMAVOLA"]:
        db.add(Team(name=op_name, is_our_team=0))
    db.commit()

# ==========================================
# 2. CONFIGURAZIONE E CSS TABLET / TOUCH
# ==========================================
st.set_page_config(page_title="Volley Scout Pro", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    /* Ottimizzazione Tablet: rimuove i padding eccessivi e adatta lo schermo */
    .block-container {
        padding-top: 0.8rem !important;
        padding-bottom: 2rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        max-width: 100% !important;
    }

    /* Nasconde elementi superflui di Streamlit per dare un look nativo da app */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Sfondo campo arancione scuro (stile Taraflex professionale) */
    div[data-testid="stVerticalBlock"]:has(> div.element-container span#court-marker) {
        background-color: #f97316 !important;
        border: 3px solid #c2410c !important;
        border-radius: 12px !important;
        padding: 12px 8px !important;
        margin-top: 5px !important;
        margin-bottom: 15px !important;
        box-shadow: inset 0 0 25px rgba(194, 65, 12, 0.35);
    }

    /* Pulsanti del campo ottimizzati per il tocco su tablet (grandi e reattivi) */
    div[class*="st-key-crt_"] button {
        border-radius: 50% !important;
        width: 76px !important;
        height: 76px !important;
        min-width: 76px !important;
        min-height: 76px !important;
        max-width: 76px !important;
        max-height: 76px !important;
        padding: 0px !important;
        margin: 5px auto !important;
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        justify-content: center !important;
        font-size: 12px !important;
        font-weight: 800 !important;
        line-height: 1.15 !important;
        border: 3px solid #1e293b !important;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2) !important;
        white-space: pre-line !important;
        background-color: #ffffff !important; 
        color: #0f172a !important;
        /* Effetto feedback al tatto */
        transition: transform 0.05s ease;
    }
    
    div[class*="st-key-crt_"] button:active {
        transform: scale(0.95);
    }

    /* Evidenziazione per il pulsante selezionato sul campo */
    div[class*="st-key-crt_"] button[kind="primary"] {
        border: 4px solid #ef4444 !important;
        box-shadow: 0 0 14px #ef4444 !important;
        background-color: #fef2f2 !important; 
    }

    /* Pulsanti della tastiera azioni (più alti e comodi da premere con le dita) */
    div[data-testid="column"] button {
        min-height: 48px !important;
        font-weight: 700 !important;
    }

    .court-header { 
        text-align: center; 
        font-weight: bold; 
        font-size: 13px;
        color: #ffffff !important; 
        margin-bottom: 2px; 
        text-shadow: 0 1px 2px rgba(0,0,0,0.3);
    }
</style>
""", unsafe_allow_html=True)

# Session State
if 'active_lineup' not in st.session_state:
    st.session_state.active_lineup = [7, 12, 9, 4, 15, 10]
if 'sel_player_num' not in st.session_state:
    st.session_state.sel_player_num = 7
if 'sel_zone' not in st.session_state:
    st.session_state.sel_zone = 6
if 'sel_skill' not in st.session_state:
    st.session_state.sel_skill = "ATTACCO"
if 'timer_start' not in st.session_state:
    st.session_state.timer_start = None
if 'timer_elapsed' not in st.session_state:
    st.session_state.timer_elapsed = 0
if 'timer_running' not in st.session_state:
    st.session_state.timer_running = False

def get_formatted_match_time():
    elapsed = st.session_state.timer_elapsed
    if st.session_state.timer_running and st.session_state.timer_start:
        elapsed += time.time() - st.session_state.timer_start
    mins, secs = divmod(int(elapsed), 60)
    return f"{mins:02d}:{secs:02d}"

all_players = db.query(Player).filter_by(team_id=default_team.id).all()
player_dict = {p.number: p for p in all_players}
opp_team = db.query(Team).filter_by(is_our_team=0).first()

# ==========================================
# 3. BARRA LATERALE
# ==========================================
st.sidebar.title("📌 NAVIGAZIONE")
menu = st.sidebar.radio("Modulo:", ["🔴 Scout Live", "📋 Gestione Squadre", "📊 Storico Partite"])

st.sidebar.divider()
st.sidebar.title("🎨 COLORE DIVISA")
col_squadra = st.sidebar.selectbox("Colore Squadra Nostra", ["blu", "rosso", "verde", "nero", "giallo"], index=0)
col_avversaria = st.sidebar.selectbox("Colore Squadra Avversaria", ["rosso", "blu", "nero", "giallo"], index=0)
col_libero = st.sidebar.selectbox("Colore Libero Nostro", ["arancione", "giallo", "bianco"], index=0)

st.sidebar.divider()
st.sidebar.title("⇄ Inverti Campo")
is_away = st.sidebar.checkbox("Trasferta", value=False)

# ==========================================
# MODALITÀ 1: SCOUT LIVE
# ==========================================
if menu == "🔴 Scout Live":
    c_head1, c_head2 = st.columns([2.2, 1.2])
    with c_head1:
        st.subheader(f"🏐 LIBERTAS SANPAOLO vs. {opp_team.name if opp_team else 'AVVERSARIO'}")
    with c_head2:
        t_col1, t_col2, t_col3, t_col4 = st.columns([1.2, 1, 1, 1])
        with t_col1:
            st.metric("⏱ TEMPO", get_formatted_match_time())
        with t_col2:
            if not st.session_state.timer_running and st.button("▶️", key="t_start", use_container_width=True):
                st.session_state.timer_start = time.time(); st.session_state.timer_running = True; st.rerun()
        with t_col3:
            if st.session_state.timer_running and st.button("⏸", key="t_pause", use_container_width=True):
                st.session_state.timer_elapsed += time.time() - st.session_state.timer_start; st.session_state.timer_running = False; st.rerun()
        with t_col4:
            if st.button("🔄", key="t_reset", use_container_width=True):
                st.session_state.timer_running = False; st.session_state.timer_start = None; st.session_state.timer_elapsed = 0; st.rerun()

    st.divider()
    col_campo, col_tastiera = st.columns([2.2, 1.1], gap="large")

    sel_num = st.session_state.sel_player_num
    sel_player_obj = player_dict.get(sel_num)
    sel_sur = sel_player_obj.surname if sel_player_obj else "ATLETA"

    with col_campo:
        st.markdown("##### 🏐 CAMPO DI GIOCO")
        
        left_name = opp_team.name if (is_away and opp_team) else "LIBERTAS SANPAOLO"
        right_name = "LIBERTAS SANPAOLO" if is_away else (opp_team.name if opp_team else "AVVERSARIO")
        left_is_our = not is_away
        
        st.markdown(f"**📍 {left_name}** {'&nbsp;'*35} 🥅 **RETE** {'&nbsp;'*35} **📍 {right_name}**")

        # CONTENITORE CAMPO ARANCIONE SCURO
        court_container = st.container()
        with court_container:
            st.markdown('<span id="court-marker"></span>', unsafe_allow_html=True)
            
            c_z561_L, c_z432_L, c_net, c_z234_R, c_z165_R = st.columns([1, 1, 0.1, 1, 1])
            p = st.session_state.active_lineup

            def get_player_circle_text(num, is_selected):
                pl = player_dict.get(num)
                sur = pl.surname if pl else str(num)
                role = pl.role if pl else ""
                icon = "⭐" if is_selected else ("🟠" if role == "L" else "🔵")
                return f"{icon} #{num}\n{sur}"

            def get_target_circle_text(zone, is_selected):
                icon = "🎯" if is_selected else "🔴"
                return f"{icon} Z{zone}\n(TGT)"

            # SINISTRA - DIFESA
            with c_z561_L:
                st.markdown('<p class="court-header">DIFESA</p>', unsafe_allow_html=True)
                for idx, z in [(5, 5), (4, 6), (3, 1)]:
                    if left_is_our:
                        n = p[idx]
                        is_sel = (n == sel_num)
                        if st.button(get_player_circle_text(n, is_sel), key=f"crt_l_{z}", type="primary" if is_sel else "secondary", use_container_width=True):
                            st.session_state.sel_player_num = n; st.rerun()
                    else:
                        is_sel = (z == st.session_state.sel_zone)
                        if st.button(get_target_circle_text(z, is_sel), key=f"crt_lo_{z}", type="primary" if is_sel else "secondary", use_container_width=True):
                            st.session_state.sel_zone = z; st.rerun()

            # SINISTRA - ATTACCO
            with c_z432_L:
                st.markdown('<p class="court-header">ATTACCO</p>', unsafe_allow_html=True)
                for idx, z in [(0, 4), (1, 3), (2, 2)]:
                    if left_is_our:
                        n = p[idx]
                        is_sel = (n == sel_num)
                        if st.button(get_player_circle_text(n, is_sel), key=f"crt_la_{z}", type="primary" if is_sel else "secondary", use_container_width=True):
                            st.session_state.sel_player_num = n; st.rerun()
                    else:
                        is_sel = (z == st.session_state.sel_zone)
                        if st.button(get_target_circle_text(z, is_sel), key=f"crt_loa_{z}", type="primary" if is_sel else "secondary", use_container_width=True):
                            st.session_state.sel_zone = z; st.rerun()

            # RETE (Linea bianca brillante)
            with c_net:
                st.markdown("<div style='background-color: #ffffff; width: 4px; height: 260px; margin: auto; border-radius: 2px; box-shadow: 0 0 6px rgba(0,0,0,0.4);'></div>", unsafe_allow_html=True)

            # DESTRA - ATTACCO
            with c_z234_R:
                st.markdown('<p class="court-header">ATTACCO</p>', unsafe_allow_html=True)
                for idx, z in [(2, 2), (1, 3), (0, 4)]:
                    if not left_is_our:
                        n = p[idx]
                        is_sel = (n == sel_num)
                        if st.button(get_player_circle_text(n, is_sel), key=f"crt_ra_{z}", type="primary" if is_sel else "secondary", use_container_width=True):
                            st.session_state.sel_player_num = n; st.rerun()
                    else:
                        is_sel = (z == st.session_state.sel_zone)
                        if st.button(get_target_circle_text(z, is_sel), key=f"crt_roa_{z}", type="primary" if is_sel else "secondary", use_container_width=True):
                            st.session_state.sel_zone = z; st.rerun()

            # DESTRA - DIFESA
            with c_z165_R:
                st.markdown('<p class="court-header">DIFESA</p>', unsafe_allow_html=True)
                for idx, z in [(3, 1), (4, 6), (5, 5)]:
                    if not left_is_our:
                        n = p[idx]
                        is_sel = (n == sel_num)
                        if st.button(get_player_circle_text(n, is_sel), key=f"crt_r_{z}", type="primary" if is_sel else "secondary", use_container_width=True):
                            st.session_state.sel_player_num = n; st.rerun()
                    else:
                        is_sel = (z == st.session_state.sel_zone)
                        if st.button(get_target_circle_text(z, is_sel), key=f"crt_ro_{z}", type="primary" if is_sel else "secondary", use_container_width=True):
                            st.session_state.sel_zone = z; st.rerun()

        st.divider()
        # PANCHINA / SOSTITUZIONI
        st.markdown(f"##### 🔄 SOSTITUZIONI (Selezionato: **#{sel_num} {sel_sur}**)")
        bench = [pl for pl in all_players if pl.number not in st.session_state.active_lineup]
        if bench:
            b_cols = st.columns(5)
            for idx, p_bench in enumerate(bench):
                with b_cols[idx % 5]:
                    if st.button(f"#{p_bench.number}\n{p_bench.surname}", key=f"sub_{p_bench.number}", use_container_width=True):
                        try:
                            lineup_idx = st.session_state.active_lineup.index(sel_num)
                            st.session_state.active_lineup[lineup_idx] = p_bench.number
                            st.session_state.sel_player_num = p_bench.number
                            db.add(SubstitutionEvent(
                                match_id=1, player_out_num=sel_num, player_out_name=sel_sur,
                                player_in_num=p_bench.number, player_in_name=p_bench.surname, match_time=get_formatted_match_time()
                            ))
                            db.commit()
                            st.toast(f"🔄 Sostituzione: #{p_bench.number} {p_bench.surname}")
                            st.rerun()
                        except ValueError:
                            st.error("Seleziona prima un'atleta in campo.")
        else:
            st.caption("Nessuna atleta in panchina.")

    # TASTIERA AZIONI
    with col_tastiera:
        st.markdown("##### ⚙️ TASTIERA AZIONI")
        st.info(f"Atleta: **#{sel_num} {sel_sur}** | Azione: **{st.session_state.sel_skill}** | Target: **Z{st.session_state.sel_zone}**")
        
        skills = ["BATTUTA", "RICEZIONE", "ALZATA", "ATTACCO", "MURO", "DIFESA"]
        sk1, sk2, sk3 = st.columns(3)
        for i, sk in enumerate(skills[:3]):
            with sk1 if i==0 else (sk2 if i==1 else sk3):
                pass
        # Semplifichiamo i pulsanti in griglia 2x3 per i tablet
        sk_c1, sk_c2 = st.columns(2)
        for i, sk in enumerate(skills[:3]):
            with sk_c1:
                if st.button(sk, key=f"sk_{sk}", type="primary" if st.session_state.sel_skill == sk else "secondary", use_container_width=True):
                    st.session_state.sel_skill = sk; st.rerun()
        for i, sk in enumerate(skills[3:]):
            with sk_c2:
                if st.button(sk, key=f"sk_{sk}", type="primary" if st.session_state.sel_skill == sk else "secondary", use_container_width=True):
                    st.session_state.sel_skill = sk; st.rerun()

        st.markdown("##### 📊 ESITO")
        evals = [("❌ Errore", "❌"), ("— Scarso", "-"), ("/ Neutro", "/"),
                 ("! Buono", "!"), ("+ Eccell.", "+"), ("# Punto", "#")]
        
        ev1, ev2 = st.columns(2)
        for i, (label, sym) in enumerate(evals[:3]):
            with ev1:
                if st.button(label, key=f"ev_{i}", use_container_width=True):
                    db.add(ScoutEvent(match_id=1, player_number=sel_num, player_surname=sel_sur, skill=st.session_state.sel_skill, evaluation=sym, target_zone=st.session_state.sel_zone, match_time=get_formatted_match_time()))
                    db.commit()
                    st.toast(f"✅ #{sel_num} {st.session_state.sel_skill} {sym} (Z{st.session_state.sel_zone})")
                    st.rerun()
        for i, (label, sym) in enumerate(evals[3:]):
            with ev2:
                if st.button(label, key=f"ev_{i+3}", use_container_width=True):
                    db.add(ScoutEvent(match_id=1, player_number=sel_num, player_surname=sel_sur, skill=st.session_state.sel_skill, evaluation=sym, target_zone=st.session_state.sel_zone, match_time=get_formatted_match_time()))
                    db.commit()
                    st.toast(f"✅ #{sel_num} {st.session_state.sel_skill} {sym} (Z{st.session_state.sel_zone})")
                    st.rerun()

        st.divider()
        st.markdown("**ULTIME AZIONI**")
        events = db.query(ScoutEvent).order_by(ScoutEvent.id.desc()).limit(4).all()
        for e in events:
            st.caption(f"⏱ **{e.match_time}** | #{e.player_number} {e.player_surname} -> {e.skill} **{e.evaluation}** (Z{e.target_zone})")

# ==========================================
# MODALITÀ 2: GESTIONE SQUADRE
# ==========================================
elif menu == "📋 Gestione Squadre":
    st.title("📋 Gestione Rosa Atlete")
    col_add, col_list = st.columns([1, 2], gap="large")
    
    with col_add:
        st.subheader("➕ Aggiungi Atleta")
        with st.form("add_player_form", clear_on_submit=True):
            new_num = st.number_input("Numero Maglia", min_value=1, max_value=99, value=10)
            new_sur = st.text_input("Cognome")
            new_role = st.selectbox("Ruolo", ["Schiacciatrice", "Palleggiatrice", "Centrale", "Opposto", "Libero"])
            if st.form_submit_button("Aggiungi in Rosa", use_container_width=True):
                if new_sur:
                    db.add(Player(team_id=default_team.id, number=new_num, surname=new_sur.upper(), role=new_role[0]))
                    db.commit()
                    st.success(f"Atleta #{new_num} aggiunta!")
                    st.rerun()
                else:
                    st.error("Inserisci il cognome.")

    with col_list:
        st.subheader("📜 Rosa Libertas Sanpaolo")
        players = db.query(Player).filter_by(team_id=default_team.id).all()
        df_players = pd.DataFrame([{"ID": p.id, "Numero": p.number, "Cognome": p.surname, "Ruolo": p.role} for p in players])
        st.dataframe(df_players, use_container_width=True, hide_index=True)

# ==========================================
# MODALITÀ 3: STORICO PARTITE
# ==========================================
elif menu == "📊 Storico Partite":
    st.title("📊 Storico Scouting")
    tab_events, tab_subs = st.tabs(["🏐 Azioni Partita", "🔄 Sostituzioni"])
    
    with tab_events:
        events = db.query(ScoutEvent).order_by(ScoutEvent.id.desc()).all()
        if events:
            df_e = pd.DataFrame([{"Tempo": e.match_time, "Giocatore": f"#{e.player_number} {e.player_surname}", "Azione": e.skill, "Esito": e.evaluation, "Zona Target": f"Z{e.target_zone}"} for e in events])
            st.dataframe(df_e, use_container_width=True, hide_index=True)
            if st.button("🗑️ Cancella Storico"):
                db.query(ScoutEvent).delete(); db.commit(); st.rerun()
        else:
            st.info("Nessuna azione registrata.")

    with tab_subs:
        subs = db.query(SubstitutionEvent).order_by(SubstitutionEvent.id.desc()).all()
        if subs:
            df_s = pd.DataFrame([{"Tempo": s.match_time, "Uscita": f"#{s.player_out_num} {s.player_out_name}", "Ingresso": f"#{s.player_in_num} {s.player_in_name}"} for s in subs])
            st.dataframe(df_s, use_container_width=True, hide_index=True)
        else:
            st.info("Nessuna sostituzione registrata.")
