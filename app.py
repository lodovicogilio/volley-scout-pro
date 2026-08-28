import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker
import datetime
import time

# ==========================================
# 1. DATABASE SETUP (Nome fisso per preservare i dati)
# ==========================================
Base = declarative_base()

class Team(Base):
    __tablename__ = 'teams'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    is_our_team = Column(Integer, default=0) # 1 = Nostra squadra, 0 = Avversaria di campionato

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
    match_id = Column(String, default="Partita 1")
    match_year = Column(Integer, default=2026)
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
    match_id = Column(String, default="Partita 1")
    match_year = Column(Integer, default=2026)
    player_out_num = Column(Integer)
    player_out_name = Column(String)
    player_in_num = Column(Integer)
    player_in_name = Column(String)
    match_time = Column(String)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

engine = create_engine('sqlite:///volley_scout_pro.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
db = Session()

# Popolamento iniziale squadra principale (solo se il database è completamente vuoto)
default_team = db.query(Team).filter_by(name="LIBERTAS SANPAOLO", is_our_team=1).first()
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

# Popolamento iniziale squadre avversarie di campionato
existing_opps = db.query(Team).filter_by(is_our_team=0).all()
if not existing_opps:
    default_opponents = ["OLYMPIA ROMA", "PRO PATRIA", "IMAVOLA", "VOLLEY LIVORNO", "VISETTE VOLLEY"]
    for op_name in default_opponents:
        db.add(Team(name=op_name, is_our_team=0))
    db.commit()

# ==========================================
# 2. CONFIGURAZIONE E CSS SPECIFICO PER TABLET / TOUCH
# ==========================================
st.set_page_config(page_title="Volley Scout Pro", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    .block-container {
        padding-top: 0.5rem !important;
        padding-bottom: 1.5rem !important;
        padding-left: 0.8rem !important;
        padding-right: 0.8rem !important;
        max-width: 100% !important;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Ottimizzazione Touch per Sidebar su Tablet */
    section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label {
        padding: 12px 10px !important;
        margin-bottom: 6px !important;
        background-color: #f1f5f9;
        border-radius: 8px;
        font-size: 15px !important;
        font-weight: 700 !important;
    }

    /* Stile campo arancione caldo con bordi bianchi netti ottimizzato touch */
    div[data-testid="stVerticalBlock"]:has(> div.element-container span#court-marker) {
        background-color: #f97316 !important;
        border: 4px solid #ffffff !important;
        border-radius: 10px !important;
        padding: 14px 10px !important;
        margin-top: 4px !important;
        margin-bottom: 10px !important;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.25);
    }

    /* Pulsanti circolari del campo (ingranditi per dita su tablet) */
    div[class*="st-key-crt_"] button {
        border-radius: 50% !important;
        width: 78px !important;
        height: 78px !important;
        min-width: 78px !important;
        min-height: 78px !important;
        max-width: 78px !important;
        max-height: 78px !important;
        padding: 0px !important;
        margin: 4px auto !important;
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
        transition: transform 0.05s ease;
    }
    
    div[class*="st-key-crt_"] button:active {
        transform: scale(0.92);
    }

    div[class*="st-key-crt_"] button[kind="primary"] {
        border: 4px solid #ef4444 !important;
        box-shadow: 0 0 14px #ef4444 !important;
        background-color: #fef2f2 !important; 
    }

    /* Pulsanti generali a misura di dito (min-height maggiore) */
    div[data-testid="column"] button {
        min-height: 52px !important;
        font-weight: 700 !important;
        font-size: 14px !important;
        border-radius: 8px !important;
    }

    .court-header { 
        text-align: center; 
        font-weight: bold; 
        font-size: 12px;
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
if 'current_year' not in st.session_state:
    st.session_state.current_year = 2026

def get_formatted_match_time():
    elapsed = st.session_state.timer_elapsed
    if st.session_state.timer_running and st.session_state.timer_start:
        elapsed += time.time() - st.session_state.timer_start
    mins, secs = divmod(int(elapsed), 60)
    return f"{mins:02d}:{secs:02d}"

all_players = db.query(Player).filter_by(team_id=default_team.id).all()
player_dict = {p.number: p for p in all_players}
opp_teams_db = db.query(Team).filter_by(is_our_team=0).all()
opp_names_list = [o.name for o in opp_teams_db]

# ==========================================
# 3. BARRA LATERALE (TABLET FRIENDLY)
# ==========================================
st.sidebar.title("📌 NAVIGAZIONE")
menu = st.sidebar.radio("Modulo:", ["🔴 Scout Live", "📋 Gestione Squadre", "👤 Dati per Giocatrice", "📊 Storico per Anno"])

st.sidebar.divider()
st.sidebar.title("⚙️ CONFIGURAZIONE")

selected_opponent = st.sidebar.selectbox("Squadra Avversaria", opp_names_list if opp_names_list else ["Nessuna Avversaria"])
match_type_str = st.sidebar.selectbox("Tipo Partita", ["Campionato", "Amichevole", "Coppa"])
st.session_state.current_year = st.sidebar.number_input("Anno", min_value=2024, max_value=2030, value=st.session_state.current_year)

match_full_name = f"Libertas Sanpaolo vs {selected_opponent} ({match_type_str}) - {st.session_state.current_year}"

st.sidebar.divider()
st.sidebar.title("⇄ Inverti Campo")
is_away = st.sidebar.checkbox("Trasferta", value=False)

# ==========================================
# MODALITÀ 1: SCOUT LIVE
# ==========================================
if menu == "🔴 Scout Live":
    c_head1, c_head2 = st.columns([2.0, 1.3])
    with c_head1:
        st.subheader(f"🏐 {match_full_name}")
    with c_head2:
        t_col1, t_col2, t_col3, t_col4 = st.columns([1.3, 1, 1, 1])
        with t_col1:
            st.metric("⏱", get_formatted_match_time())
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
    col_campo, col_tastiera = st.columns([2.1, 1.2], gap="medium")

    sel_num = st.session_state.sel_player_num
    sel_player_obj = player_dict.get(sel_num)
    sel_sur = sel_player_obj.surname if sel_player_obj else "ATLETA"

    with col_campo:
        st.markdown("##### 🏐 CAMPO DI GIOCO")
        
        left_name = selected_opponent if is_away else "LIBERTAS SANPAOLO"
        right_name = "LIBERTAS SANPAOLO" if is_away else selected_opponent
        left_is_our = not is_away
        
        st.markdown(f"**📍 {left_name}** {'&nbsp;'*25} 🥅 **RETE** {'&nbsp;'*25} **📍 {right_name}**")

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

            with c_net:
                st.markdown("<div style='background-color: #ffffff; width: 4px; height: 250px; margin: auto; border-radius: 2px; box-shadow: 0 0 6px rgba(0,0,0,0.4);'></div>", unsafe_allow_html=True)

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
                                match_id=match_full_name, match_year=st.session_state.current_year,
                                player_out_num=sel_num, player_out_name=sel_sur,
                                player_in_num=p_bench.number, player_in_name=p_bench.surname, match_time=get_formatted_match_time()
                            ))
                            db.commit()
                            st.toast(f"🔄 Sostituzione: #{p_bench.number} {p_bench.surname}")
                            st.rerun()
                        except ValueError:
                            st.error("Seleziona prima un'atleta in campo.")
        else:
            st.caption("Nessuna atleta in panchina.")

    with col_tastiera:
        st.markdown("##### ⚙️ TASTIERA AZIONI")
        st.info(f"Atleta: **#{sel_num} {sel_sur}** | Azione: **{st.session_state.sel_skill}** | Target: **Z{st.session_state.sel_zone}**")
        
        skills = ["BATTUTA", "RICEZIONE", "ALZATA", "ATTACCO", "MURO", "DIFESA"]
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
        evals = ["Errore", "Scarso", "Neutro", "Buono", "Ottimo", "Punto"]
        
        ev1, ev2 = st.columns(2)
        for i, val in enumerate(evals[:3]):
            with ev1:
                if st.button(val, key=f"ev_{i}", use_container_width=True):
                    db.add(ScoutEvent(
                        match_id=match_full_name, match_year=st.session_state.current_year,
                        player_number=sel_num, player_surname=sel_sur, skill=st.session_state.sel_skill, 
                        evaluation=val, target_zone=st.session_state.sel_zone, match_time=get_formatted_match_time()
                    ))
                    db.commit()
                    st.toast(f"✅ #{sel_num} {st.session_state.sel_skill}: {val} (Z{st.session_state.sel_zone})")
                    st.rerun()
        for i, val in enumerate(evals[3:]):
            with ev2:
                if st.button(val, key=f"ev_{i+3}", use_container_width=True):
                    db.add(ScoutEvent(
                        match_id=match_full_name, match_year=st.session_state.current_year,
                        player_number=sel_num, player_surname=sel_sur, skill=st.session_state.sel_skill, 
                        evaluation=val, target_zone=st.session_state.sel_zone, match_time=get_formatted_match_time()
                    ))
                    db.commit()
                    st.toast(f"✅ #{sel_num} {st.session_state.sel_skill}: {val} (Z{st.session_state.sel_zone})")
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
    st.title("📋 Gestione Database Squadre e Atlete")
    
    tab_squadre, tab_atlete = st.tabs(["🏛️ Squadre di Campionato", "👥 Rosa Libertas Sanpaolo"])
    
    with tab_squadre:
        col_add_op, col_list_op = st.columns([1, 2], gap="large")
        with col_add_op:
            st.subheader("➕ Aggiungi Squadra Avversaria")
            with st.form("add_opponent_form", clear_on_submit=True):
                new_op_name = st.text_input("Nome Società / Squadra")
                if st.form_submit_button("Salva nel Campionato", use_container_width=True):
                    if new_op_name:
                        exists = db.query(Team).filter_by(name=new_op_name.upper()).first()
                        if not exists:
                            db.add(Team(name=new_op_name.upper(), is_our_team=0))
                            db.commit()
                            st.success(f"Squadra '{new_op_name.upper()}' aggiunta con successo!")
                            st.rerun()
                        else:
                            st.error("Questa squadra è già presente nel database.")
                    else:
                        st.error("Inserisci il nome della squadra.")
        
        with col_list_op:
            st.subheader("📜 Elenco Squadre Avversarie Registrate")
            current_opps = db.query(Team).filter_by(is_our_team=0).all()
            df_opps = pd.DataFrame([{"ID": o.id, "Squadra Avversaria": o.name} for o in current_opps])
            st.dataframe(df_opps, use_container_width=True, hide_index=True)
            
            if current_opps:
                del_op = st.selectbox("Seleziona squadra da eliminare", [o.name for o in current_opps])
                if st.button("🗑️ Elimina Squadra Selezionata"):
                    team_to_del = db.query(Team).filter_by(name=del_op, is_our_team=0).first()
                    if team_to_del:
                        db.delete(team_to_del)
                        db.commit()
                        st.success(f"Squadra {del_op} eliminata.")
                        st.rerun()

    with tab_atlete:
        col_add_edit, col_list_pl = st.columns([1, 1.5], gap="large")
        
        with col_add_edit:
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

            st.divider()
            st.subheader("✏️ Modifica o Elimina Atleta")
            players_edit_list = db.query(Player).filter_by(team_id=default_team.id).all()
            if players_edit_list:
                player_options = {f"#{p.number} {p.surname}": p for p in players_edit_list}
                selected_p_key = st.selectbox("Seleziona atleta", list(player_options.keys()), key="sel_mod_player")
                selected_player = player_options[selected_p_key]
                
                with st.form("edit_player_form"):
                    edit_num = st.number_input("Nuovo Numero", min_value=1, max_value=99, value=selected_player.number)
                    edit_sur = st.text_input("Nuovo Cognome", value=selected_player.surname)
                    roles_list = ["Schiacciatrice", "Palleggiatrice", "Centrale", "Opposto", "Libero"]
                    role_map = {"S": "Schiacciatrice", "P": "Palleggiatrice", "C": "Centrale", "O": "Opposto", "L": "Libero"}
                    curr_full = role_map.get(selected_player.role, "Schiacciatrice")
                    edit_role = st.selectbox("Nuovo Ruolo", roles_list, index=roles_list.index(curr_full) if curr_full in roles_list else 0)
                    
                    c_e1, c_e2 = st.columns(2)
                    with c_e1:
                        btn_save = st.form_submit_button("💾 Salva", use_container_width=True)
                    with c_e2:
                        btn_del = st.form_submit_button("🗑️ Elimina", use_container_width=True)
                        
                    if btn_save:
                        selected_player.number = edit_num
                        selected_player.surname = edit_sur.upper()
                        selected_player.role = edit_role[0]
                        db.commit()
                        st.success("Modifiche salvate con successo!")
                        st.rerun()
                    if btn_del:
                        db.delete(selected_player)
                        db.commit()
                        st.success("Atleta eliminata.")
                        st.rerun()
            else:
                st.caption("Nessuna atleta disponibile.")

        with col_list_pl:
            st.subheader("📜 Rosa Libertas Sanpaolo")
            players = db.query(Player).filter_by(team_id=default_team.id).all()
            df_players = pd.DataFrame([{"ID": p.id, "Numero": p.number, "Cognome": p.surname, "Ruolo": p.role} for p in players])
            st.dataframe(df_players, use_container_width=True, hide_index=True)

# ==========================================
# MODALITÀ 3: DATI PER GIOCATRICE
# ==========================================
elif menu == "👤 Dati per Giocatrice":
    st.title("👤 Analisi Dettagliata per Giocatrice")
    
    col_sel1, col_sel2 = st.columns(2)
    with col_sel1:
        player_names_list = [f"#{p.number} {p.surname}" for p in all_players]
        selected_p_str = st.selectbox("Seleziona Atleta", player_names_list)
    with col_sel2:
        matches_list = [m[0] for m in db.query(ScoutEvent.match_id).distinct().all()]
        selected_match_filter = st.selectbox("Filtra per Partita", ["Tutte le partite"] + matches_list)

    if selected_p_str:
        p_num_extracted = int(selected_p_str.split(" ")[0].replace("#", ""))
        
        query_events = db.query(ScoutEvent).filter_by(player_number=p_num_extracted)
        if selected_match_filter != "Tutte le partite":
            query_events = query_events.filter_by(match_id=selected_match_filter)
        
        player_events = query_events.order_by(ScoutEvent.id.desc()).all()
        
        st.divider()
        st.subheader(f"Statistiche e Azioni per: {selected_p_str}")
        
        if player_events:
            df_pe = pd.DataFrame([{
                "Partita": e.match_id,
                "Anno": e.match_year,
                "Tempo": e.match_time,
                "Azione": e.skill,
                "Esito": e.evaluation,
                "Zona Target": f"Z{e.target_zone}"
            } for e in player_events])
            
            kpi1, kpi2, kpi3 = st.columns(3)
            with kpi1:
                st.metric("Totale Azioni", len(df_pe))
            with kpi2:
                punti = len(df_pe[df_pe["Esito"] == "Punto"])
                st.metric("Punti", punti)
            with kpi3:
                errori = len(df_pe[df_pe["Esito"] == "Errore"])
                st.metric("Errori", errori)

            st.markdown("##### Dettaglio Cronologico Azioni")
            st.dataframe(df_pe, use_container_width=True, hide_index=True)
        else:
            st.info("Nessuna azione registrata per i filtri selezionati.")

# ==========================================
# MODALITÀ 4: STORICO PER ANNO
# ==========================================
elif menu == "📊 Storico per Anno":
    st.title("📊 Storico Partite Diviso per Anno")
    
    available_years = [y[0] for y in db.query(ScoutEvent.match_year).distinct().order_by(ScoutEvent.match_year.desc()).all()]
    if not available_years:
        available_years = [2026]
        
    selected_year = st.selectbox("Seleziona Anno di Riferimento", available_years)
    
    st.divider()
    
    year_events = db.query(ScoutEvent).filter_by(match_year=selected_year).order_by(ScoutEvent.id.desc()).all()
    year_subs = db.query(SubstitutionEvent).filter_by(match_year=selected_year).order_by(SubstitutionEvent.id.desc()).all()
    
    tab_ist_events, tab_ist_subs = st.tabs([f"🏐 Azioni ({selected_year})", f"🔄 Sostituzioni ({selected_year})"])
    
    with tab_ist_events:
        if year_events:
            df_ye = pd.DataFrame([{
                "Partita": e.match_id,
                "Tempo": e.match_time,
                "Giocatore": f"#{e.player_number} {e.player_surname}",
                "Azione": e.skill,
                "Esito": e.evaluation,
                "Zona Target": f"Z{e.target_zone}"
            } for e in year_events])
            st.dataframe(df_ye, use_container_width=True, hide_index=True)
        else:
            st.info(f"Nessuna azione registrata per l'anno {selected_year}.")

    with tab_ist_subs:
        if year_subs:
            df_ys = pd.DataFrame([{
                "Partita": s.match_id,
                "Tempo": s.match_time,
                "Uscita": f"#{s.player_out_num} {s.player_out_name}",
                "Ingresso": f"#{s.player_in_num} {s.player_in_name}"
            } for s in year_subs])
            st.dataframe(df_ys, use_container_width=True, hide_index=True)
        else:
            st.info(f"Nessuna sostituzione registrata per l'anno {selected_year}.")
