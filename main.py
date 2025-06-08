import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image, ImageFilter
import os
import base64


def get_image_path(folder, filename):
    for ext in [".png", ".webp"]:
        path = os.path.join(folder, f"{filename}{ext}")
        if os.path.exists(path):
            return path
    return None


def get_team_logo_filename(team):
    mapping = {
        "LNG": "LNG_esports",
        "WBG": "WBG_gaming",
        "HLE": "HLE_esports",
        "BLG": "BLG_gaming",
        "TES": "TES_esports",
        "T1": "T1_esports",
        "FLY": "FLY_esports",
        "GEN": "GENG_esports"
    }
    return mapping.get(team, team)


@st.cache_data
def load_data():
    file_path = "2024 Worlds Quarter - Finals.xlsx"
    if not os.path.exists(file_path):
        st.error(f"Excel file not found at {file_path}")
        return pd.DataFrame()

    try:
        sheets_to_load = ["Quarterfinals", "Semifinals", "Finals"]
        xl = pd.read_excel(file_path, sheet_name=sheets_to_load)
        stages = []
        for stage in sheets_to_load:
            if stage in xl:
                temp = xl[stage].copy()
                temp["Stage"] = stage
                stages.append(temp)
            else:
                st.warning(f"Sheet '{stage}' not found in the Excel file.")
        data = pd.concat(stages, ignore_index=True)
        # Process Banned Champions column safely.
        if "Banned Champions" in data.columns:
            data["Banned Champions"] = data["Banned Champions"].fillna("").apply(
                lambda x: [champ.strip() for champ in x.split(",") if champ.strip()]
            )
        else:
            st.warning("Column 'Banned Champions' not found in the data.")
        return data
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()


def set_bg_image(image_path):
    if os.path.exists(image_path):
        img = Image.open(image_path).convert("RGB")
        img = img.filter(ImageFilter.GaussianBlur(5))
        temp_path = "temp_blurred_bg.png"
        img.save(temp_path)
        with open(temp_path, "rb") as image_file:
            encoded = base64.b64encode(image_file.read()).decode()
        css = f"""
            <style>
            .stApp {{
                background-image: url("data:image/png;base64,{encoded}");
                background-size: cover;
                background-attachment: fixed;
            }}
            </style>
        """
        st.markdown(css, unsafe_allow_html=True)
    else:
        st.info("Background image file not found.")


set_bg_image("images/bg/background_img.png")

with st.spinner("Loading data..."):
    df = load_data()

if df.empty:
    st.error("Data failed to load. Please check the Excel file and its sheets.")
    st.stop()

st.title("2024 League of Legends Worlds [Quarterfinals to Finals Statistics]")


stage_filter = st.sidebar.multiselect("Select Stage",
                                      options=df["Stage"].unique(),
                                      default=list(df["Stage"].unique()))
if "Team" not in df.columns:
    st.error("No 'Team' column found in the data.")
    st.stop()
teams = df["Team"].unique()
team_filter = st.sidebar.selectbox("Select Team", options=teams)

filtered_df = df[df["Stage"].isin(stage_filter)]
filtered_team_df = filtered_df[filtered_df["Team"] == team_filter]


highlight_tab, tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🎮 Highlights",
    "Player Stats",
    "Pick/Ban Trends",
    "Match Summaries",
    "Win Rates",
    "All Team Stats"
])


with highlight_tab:
    st.header("Match Highlights")
    st.video("https://youtu.be/5bgl3b09hqQ")  # Quarterfinals
    st.video("https://youtu.be/elBETWSuMSs")  # Semifinals
    st.video("https://youtu.be/vlRt36fKgaw")  # Finals


with tab1:
    st.header(f"Player Stats for {team_filter}")

    logo_filename = get_team_logo_filename(team_filter)
    logo_path = get_image_path("images/logos", logo_filename)
    if logo_path:
        logo = Image.open(logo_path)
        st.image(logo, width=120)
    else:
        st.warning(f"Team logo for {team_filter} not found.")

    if "Player IGN" not in filtered_team_df.columns:
        st.error("Column 'Player IGN' not found in the data.")
    else:
        players = filtered_team_df["Player IGN"].unique()
        if not players.size:
            st.error("No player data found for the selected team.")
        else:
            player = st.selectbox("Select Player", options=players)
            player_stats = filtered_team_df[filtered_team_df["Player IGN"] == player]


            if "_" not in player:
                player_for_image = team_filter + "_" + player
            else:
                player_for_image = player

            player_img_path = get_image_path("images/players", player_for_image)
            if player_img_path:
                player_img = Image.open(player_img_path)
                st.image(player_img, width=120)
            else:
                st.warning(f"Player image for {player_for_image} not found.")

            if "Player Real Name" in player_stats.columns:
                real_name = player_stats["Player Real Name"].iloc[0]
                st.markdown(f"**Real Name:** {real_name}")

            if not player_stats.empty:
                stats = player_stats[
                    ["Stage", "Match No", "Champion", "Kills", "Deaths", "Assists", "CS", "Gold", "CS/Min",
                     "GPM"]].copy()
                stats["CS/Min"] = stats["CS/Min"].round(1)
                stats["GPM"] = stats["GPM"].round(1)
                st.dataframe(stats)

                kda = player_stats[["Kills", "Deaths", "Assists"]].sum()
                avg_cs_min = player_stats["CS/Min"].mean()
                avg_gpm = player_stats["GPM"].mean()

                st.markdown(f"**Total KDA:** {kda['Kills']}/{kda['Deaths']}/{kda['Assists']}")
                st.markdown(f"**Average CS/Min:** {avg_cs_min:.1f}")
                st.markdown(f"**Average GPM:** {avg_gpm:.1f}")
            else:
                st.info("Player stats are empty.")


with tab2:
    st.header("Champion Pick/Ban Trends")

    if "Champion" not in df.columns:
        st.error("Column 'Champion' not found in the data.")
    else:
        all_champs = df["Champion"].value_counts().reset_index()
        all_champs.columns = ["Champion", "Pick Count"]
        ban_counts = df["Banned Champions"].explode().value_counts().reset_index()
        ban_counts.columns = ["Champion", "Ban Count"]

        merged = pd.merge(all_champs, ban_counts, on="Champion", how="outer").fillna(0)
        merged = merged.sort_values(by="Pick Count", ascending=False)

        fig = px.bar(
            merged,
            x="Champion",
            y=["Pick Count", "Ban Count"],
            barmode="group",
            title="Pick vs Ban Count"
        )
        st.plotly_chart(fig)


with tab3:
    st.header("Match Summaries")

    necessary_cols = ["Stage", "Match No", "Duration (min)", "Kills", "Deaths", "Assists", "Gold", "CS"]
    if not all(col in df.columns for col in necessary_cols):
        st.error("One or more required columns for match summaries are missing in the data.")
    else:
        match_summary = df.groupby(["Stage", "Match No"]).agg({
            "Duration (min)": "mean",
            "Kills": "sum",
            "Deaths": "sum",
            "Assists": "sum",
            "Gold": "sum",
            "CS": "sum"
        }).reset_index()

        match_summary["KDA"] = (
                match_summary["Kills"].astype(str) + "/" +
                match_summary["Deaths"].astype(str) + "/" +
                match_summary["Assists"].astype(str)
        )
        match_summary["Gold/Min"] = (match_summary["Gold"] / match_summary["Duration (min)"]).round(1)
        match_summary["CS/Min"] = (match_summary["CS"] / match_summary["Duration (min)"]).round(1)
        match_summary["Duration (min)"] = match_summary["Duration (min)"].round(1)

        st.dataframe(match_summary[["Stage", "Match No", "KDA", "Gold/Min", "CS/Min", "Duration (min)"]])


with tab4:
    st.header("Champion and Team Win Rates")

    if not all(col in df.columns for col in ["Team", "Gold", "Champion"]):
        st.error("One or more required columns for win rate calculations are missing.")
    else:
        match_avg_gold = df.groupby(["Stage", "Match No", "Team"]).agg({"Gold": "mean"}).reset_index()
        match_winners = match_avg_gold.loc[match_avg_gold.groupby(["Stage", "Match No"])["Gold"].idxmax()]
        match_winners = match_winners.rename(columns={"Team": "Winning Team"})

        df_with_win = pd.merge(df, match_winners[["Stage", "Match No", "Winning Team"]], on=["Stage", "Match No"],
                               how="left")
        df_with_win["Won"] = df_with_win["Team"] == df_with_win["Winning Team"]

        champ_wins = df_with_win[df_with_win["Won"]].groupby("Champion").size().reset_index(name="Wins")
        champ_total = df_with_win.groupby("Champion").size().reset_index(name="Games")
        champ_wr = pd.merge(champ_total, champ_wins, on="Champion", how="left").fillna(0)
        champ_wr["Win Rate (%)"] = ((champ_wr["Wins"] / champ_wr["Games"]) * 100).round(1)
        champ_wr = champ_wr.sort_values(by="Win Rate (%)", ascending=False)

        st.subheader("Champion Win Rates")
        st.dataframe(champ_wr[["Champion", "Games", "Wins", "Win Rate (%)"]])

        team_wins = df_with_win[df_with_win["Won"]].groupby("Team").size().reset_index(name="Wins")
        team_total = df_with_win.groupby("Team").size().reset_index(name="Games")
        team_wr = pd.merge(team_total, team_wins, on="Team", how="left").fillna(0)
        team_wr["Win Rate (%)"] = ((team_wr["Wins"] / team_wr["Games"]) * 100).round(1)
        team_wr = team_wr.sort_values(by="Win Rate (%)", ascending=False)

        st.subheader("Team Win Rates")
        st.dataframe(team_wr[["Team", "Games", "Wins", "Win Rate (%)"]])


with tab5:
    st.header("All Team Stats")

    stats_cols = ["Team", "Kills", "Deaths", "Assists", "Gold", "CS", "CS/Min", "GPM"]
    if not all(col in df.columns for col in stats_cols):
        st.error("One or more required columns for team statistics are missing.")
    else:
        team_stats = df.groupby("Team").agg({
            "Kills": ["sum", "mean"],
            "Deaths": ["sum", "mean"],
            "Assists": ["sum", "mean"],
            "Gold": ["sum", "mean"],
            "CS": ["sum", "mean"],
            "CS/Min": "mean",
            "GPM": "mean"
        })

        team_stats.columns = ['_'.join(col).strip() for col in team_stats.columns.values]
        team_stats = team_stats.reset_index()

        for col in team_stats.columns:
            if team_stats[col].dtype in ['float64', 'float32']:
                team_stats[col] = team_stats[col].round(1)

        st.subheader("Team Statistics with Logos")
        for index, row in team_stats.iterrows():
            cols = st.columns([1, 4])
            team_logo_filename = get_team_logo_filename(row["Team"])
            team_logo = get_image_path("images/logos", team_logo_filename)
            if team_logo:
                cols[0].image(team_logo, width=60)
            else:
                cols[0].warning("No logo")
            stats_md = (
                f"**Team:** {row['Team']}\n\n"
                f"**Kills:** {row['Kills_sum']} (avg: {row['Kills_mean']})\n\n"
                f"**Deaths:** {row['Deaths_sum']} (avg: {row['Deaths_mean']})\n\n"
                f"**Assists:** {row['Assists_sum']} (avg: {row['Assists_mean']})\n\n"
                f"**Gold:** {row['Gold_sum']} (avg: {row['Gold_mean']})\n\n"
                f"**CS:** {row['CS_sum']} (avg: {row['CS_mean']})\n\n"
                f"**CS/Min:** {row['CS/Min_mean']}\n\n"
                f"**GPM:** {row['GPM_mean']}"
            )
            cols[1].markdown(stats_md)
