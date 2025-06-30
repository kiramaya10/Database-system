import streamlit as st
import pandas as pd
import json
import os
import altair as alt
from datetime import date


def load_user_data(username):
    exercise_file = f"data/{username}_exercises.json"
    diet_file = f"data/{username}_diet.json"
    exercises, diet = [], []
    if os.path.exists(exercise_file):
        with open(exercise_file, 'r') as f:
            exercises = json.load(f)
    if os.path.exists(diet_file):
        with open(diet_file, 'r') as f:
            diet = json.load(f)
    return exercises, diet

def save_user_data(username, exercises, diet):
    os.makedirs("data", exist_ok=True)
    with open(f"data/{username}_exercises.json", 'w') as f:
        json.dump(exercises, f)
    with open(f"data/{username}_diet.json", 'w') as f:
        json.dump(diet, f)

def get_existing_usernames():
    if not os.path.exists("data"):
        return []
    return sorted(set(
        f.split("_")[0] for f in os.listdir("data") if f.endswith("_exercises.json")
    ))


os.makedirs("data", exist_ok=True)
st.set_page_config(page_title="Gym Tracker", layout="wide")
st.title("🏋️ Gym Tracker App")


username_file = "data/last_user.txt"
default_username = ""
if os.path.exists(username_file):
    with open(username_file, "r") as f:
        default_username = f.read().strip()


existing_users = get_existing_usernames()
selected = st.selectbox("Select your user:", options=existing_users + ["➕ New user..."])

if selected == "➕ New user...":
    username = st.text_input("Enter new username:", value="")
else:
    username = selected

if username:
    with open(username_file, "w") as f:
        f.write(username)

    if f'exercises_{username}' not in st.session_state or f'diet_log_{username}' not in st.session_state:
        exercises, diet = load_user_data(username)
        st.session_state[f'exercises_{username}'] = exercises
        st.session_state[f'diet_log_{username}'] = diet

   
    st.markdown("### 👤 Profile")
    with st.container():
        col1, col2 = st.columns([1, 5])
        with col1:
            st.image("https://cdn-icons-png.flaticon.com/512/2922/2922510.png", width=64)
        with col2:
            st.markdown(f"**Welcome, `{username}`!**")
            st.caption(f"📅 Today is {date.today().strftime('%A, %d %B %Y')}")

   
    goal_file = f"data/{username}_goal.txt"
    default_goal = ""
    if os.path.exists(goal_file):
        with open(goal_file, "r") as f:
            default_goal = f.read().strip()

    goal = st.text_input("🎯 Set your fitness goal:", value=default_goal)
    if st.button("📂 Save Goal"):
        with open(goal_file, "w") as f:
            f.write(goal)
        st.success("Goal saved!")

    if goal:
        st.info(f"Your current goal: **{goal}**")

    #Tabs
    tab1, tab2 = st.tabs(["💪 Exercise", "🍽️ Diet"])

    #Exercise Tab 
    with tab1:
        st.header("Exercise Tracker")
        exercise_types = ["Strength", "Cardio", "Mobility", "Flexibility"]
        muscle_groups = ["Chest", "Back", "Legs", "Arms", "Shoulders", "Core", "Full Body"]

        exercise_name = st.text_input("Exercise Name")
        exercise_type = st.selectbox("Type of Exercise", exercise_types)
        muscles = st.multiselect("Targeted Muscle Groups", muscle_groups)
        exercise_date = st.date_input("Date", value=date.today())

        st.subheader("Sets")
        sets = []
        num_sets = st.number_input("How many sets?", min_value=1, max_value=10, step=1)

        for i in range(num_sets):
            col1, col2 = st.columns(2)
            with col1:
                reps = st.number_input(f"Set {i+1} Reps", min_value=1, step=1, key=f"reps_{i}")
            with col2:
                weight = st.number_input(f"Set {i+1} Weight (kg)", min_value=0.0, step=0.5, key=f"weight_{i}")
            sets.append({"Reps": reps, "Weight": weight})

        if st.button("Add Exercise"):
            if exercise_name and sets:
                st.session_state[f'exercises_{username}'].append({
                    "Exercise": exercise_name,
                    "Type": exercise_type,
                    "Muscles": ", ".join(muscles),
                    "Sets": sets,
                    "Date": str(exercise_date)
                })
                save_user_data(
                    username,
                    st.session_state[f'exercises_{username}'],
                    st.session_state[f'diet_log_{username}']
                )
                st.success(f"Logged {exercise_name} on {exercise_date}")
                st.rerun()
            else:
                st.warning("Please fill out the form completely.")

        rows = []
        for entry in st.session_state[f'exercises_{username}']:
            for i, s in enumerate(entry["Sets"]):
                rows.append({
                    "Date": entry["Date"],
                    "Exercise": entry["Exercise"],
                    "Type": entry["Type"],
                    "Muscles": entry["Muscles"],
                    "Set": i + 1,
                    "Reps": s["Reps"],
                    "Weight (kg)": s["Weight"]
                })

        if rows:
            st.subheader("Exercise Log")
            df = pd.DataFrame(rows)

            st.download_button("📄 Download CSV", df.to_csv(index=False), f"{username}_workouts.csv", "text/csv")

            delete_idx = st.selectbox(
                "Select a log to delete:",
                options=list(df.index),
                format_func=lambda x: f"{df.loc[x, 'Date']} - {df.loc[x, 'Exercise']} - Set {df.loc[x, 'Set']}"
            )

            if st.button("Delete Selected Exercise"):
                row = df.loc[delete_idx]
                original_entry_index = next(
                    i for i, e in enumerate(st.session_state[f'exercises_{username}'])
                    if e["Exercise"] == row["Exercise"] and str(e["Date"]) == row["Date"]
                )
                st.session_state[f'exercises_{username}'][original_entry_index]["Sets"].pop(row["Set"] - 1)
                if not st.session_state[f'exercises_{username}'][original_entry_index]["Sets"]:
                    st.session_state[f'exercises_{username}'].pop(original_entry_index)
                save_user_data(
                    username,
                    st.session_state[f'exercises_{username}'],
                    st.session_state[f'diet_log_{username}']
                )
                st.success("Exercise entry deleted!")
                st.rerun()

            st.dataframe(df)

            st.subheader("📈 Progress & Personal Records")
            selected_exercise = st.selectbox("View progress for:", df["Exercise"].unique())
            filtered = df[df["Exercise"] == selected_exercise].copy()
            filtered["Date"] = pd.to_datetime(filtered["Date"])

            weight_progress = filtered.groupby("Date")["Weight (kg)"].max().reset_index()
            reps_progress = filtered.groupby("Date")["Reps"].max().reset_index()

            chart_weight = alt.Chart(weight_progress).mark_line(point=True).encode(
                x=alt.X('Date:T', title='Date'),
                y=alt.Y('Weight (kg):Q', title='Max Weight (kg)'),
                tooltip=['Date:T', 'Weight (kg):Q']
            ).properties(
                title=f"{selected_exercise} - Max Weight Over Time",
                width=700, height=300
            ).configure_title(fontSize=16)

            chart_reps = alt.Chart(reps_progress).mark_line(point=True, color='green').encode(
                x=alt.X('Date:T', title='Date'),
                y=alt.Y('Reps:Q', title='Max Reps'),
                tooltip=['Date:T', 'Reps:Q']
            ).properties(
                title=f"{selected_exercise} - Max Reps Over Time",
                width=700, height=300
            ).configure_title(fontSize=16)

            st.altair_chart(chart_weight, use_container_width=True)
            st.altair_chart(chart_reps, use_container_width=True)

            max_weight = filtered["Weight (kg)"].max()
            max_reps = filtered["Reps"].max()
            st.info(f"🏆 **PR for {selected_exercise}**\n\n- Max Weight: **{max_weight} kg**\n- Max Reps: **{max_reps}**")


    #Diet Tab 
    with tab2:
        st.header("Diet Log")
        st.markdown("### 📝 Log Your Meal")

        with st.form("meal_form"):
            food_item = st.text_area("What did you eat?")
            diet_date = st.date_input("Date of meal", value=date.today(), key="diet_date")

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                calories = st.number_input("Calories", min_value=0, step=10)
            with col2:
                protein = st.number_input("Protein (g)", min_value=0, step=1)
            with col3:
                carbs = st.number_input("Carbs (g)", min_value=0, step=1)
            with col4:
                fats = st.number_input("Fats (g)", min_value=0, step=1)

            submitted = st.form_submit_button("Add Meal")

        if submitted:
            if food_item:
                st.session_state[f'diet_log_{username}'].append({
                    "Food": food_item,
                    "Date": str(diet_date),
                    "Calories": calories,
                    "Protein": protein,
                    "Carbs": carbs,
                    "Fats": fats
                })
                save_user_data(
                    username,
                    st.session_state[f'exercises_{username}'],
                    st.session_state[f'diet_log_{username}']
                )
                st.success(f"Logged meal on {diet_date}")
                st.rerun()
            else:
                st.warning("Please enter what you ate.")

        if st.session_state[f'diet_log_{username}']:
            st.subheader("Diet History")
            diet_df = pd.DataFrame(st.session_state[f'diet_log_{username}'])

            dates = diet_df["Date"].unique()
            selected_day = st.selectbox("📅 View totals for:", options=sorted(dates, reverse=True))
            totals = diet_df[diet_df["Date"] == selected_day][["Calories", "Protein", "Carbs", "Fats"]].sum()

            st.metric("Total Calories", f"{totals['Calories']} kcal")
            col1, col2, col3 = st.columns(3)
            col1.metric("Protein", f"{totals['Protein']} g")
            col2.metric("Carbs", f"{totals['Carbs']} g")
            col3.metric("Fats", f"{totals['Fats']} g")

            delete_diet_idx = st.selectbox(
                "Select a meal to delete:",
                options=list(diet_df.index),
                format_func=lambda x: f"{diet_df.loc[x, 'Date']} - {diet_df.loc[x, 'Food'][:30]}"
            )

            if st.button("Delete Selected Meal"):
                st.session_state[f'diet_log_{username}'].pop(delete_diet_idx)
                save_user_data(
                    username,
                    st.session_state[f'exercises_{username}'],
                    st.session_state[f'diet_log_{username}']
                )
                st.success("Meal entry deleted!")
                st.rerun()

            st.dataframe(diet_df)

else:
    st.info("Please select or enter a username to begin.")
