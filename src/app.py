import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import date, timedelta

# --------------------------------------------------------
# DATABASE CONNECTION
# --------------------------------------------------------
schema   = "lianes_library"
host     = "127.0.0.1"
user     = "root"
password = "REMOVED_SECRET"   # <-- change this
port     = 3306

con = f'mysql+pymysql://{user}:{password}@{host}:{port}/{schema}'
engine = create_engine(con)

# --------------------------------------------------------
# HELPER: run UPDATE / INSERT / DELETE queries
# --------------------------------------------------------
def run_query(query, params={}):
    with engine.connect() as conn:
        t = conn.begin()
        try:
            conn.execute(text(query), params)
            t.commit()
        except:
            t.rollback()
            raise

# --------------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------------
st.set_page_config(page_title="📚 Liane's Library", layout="wide", page_icon="📚")

# --------------------------------------------------------
# SESSION STATE — remember which page we are on
# --------------------------------------------------------
if "page" not in st.session_state:
    st.session_state.page = "🏠 Dashboard"

# --------------------------------------------------------
# SIDEBAR NAVIGATION
# --------------------------------------------------------
with st.sidebar:
    st.title("📚 Liane's Library")
    st.markdown("---")
    for p in ["🏠 Dashboard", "📖 Books", "👥 Friends",
              "📤 Lend a Book", "📥 Return a Book", "📋 All Loans"]:
        if st.button(p, key=p):
            st.session_state.page = p

page = st.session_state.page

# --------------------------------------------------------
# PAGE: DASHBOARD
# --------------------------------------------------------
if page == "🏠 Dashboard":
    st.title("🏠 Dashboard")
    st.markdown("Welcome to Liane's Library!")
    st.markdown("---")

    # Load data
    books   = pd.read_sql("SELECT * FROM books", con=con)
    loans   = pd.read_sql("SELECT * FROM loans", con=con)
    friends = pd.read_sql("SELECT * FROM friends", con=con)

    # KPI numbers
    total     = len(books)
    available = int(books["is_available"].sum())
    on_loan   = total - available
    cutoff  = date.today() - timedelta(days=30)
    overdue = len(loans[(loans["return_date"].isna()) & (pd.to_datetime(loans["loan_date"]).dt.date < cutoff)])

    # Show KPI cards
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📚 Total Books",          total)
    c2.metric("✅ Available",             available)
    c3.metric("📤 On Loan",              on_loan)
    c4.metric("⚠️ Overdue (30+ days)",  overdue)

    st.markdown("---")

    # Quick action buttons
    st.subheader("Quick Actions")
    b1, b2, b3, b4 = st.columns(4)
    if b1.button("➕ Add a Book"):
        st.session_state.page = "📖 Books"
        st.rerun()
    if b2.button("➕ Add a Friend"):
        st.session_state.page = "👥 Friends"
        st.rerun()
    if b3.button("📤 Lend a Book"):
        st.session_state.page = "📤 Lend a Book"
        st.rerun()
    if b4.button("📥 Return a Book"):
        st.session_state.page = "📥 Return a Book"
        st.rerun()

    st.markdown("---")

    # Who has what
    st.subheader("📋 Who Has What Right Now")
    active = pd.read_sql("""
        SELECT b.title AS Book, f.name_ AS "Borrowed By",
               f.phone_number AS Contact, l.loan_date AS Since
        FROM loans l
        JOIN books b ON l.book_id = b.ISBN
        JOIN friends f ON l.friend_id = f.friend_id
        WHERE l.return_date IS NULL
    """, con=con)

    if active.empty:
        st.success("🎉 All books are currently available!")
    else:
        st.dataframe(active, use_container_width=True, hide_index=True, height=400)

# --------------------------------------------------------
# PAGE: BOOKS
# --------------------------------------------------------
elif page == "📖 Books":
    st.title("📖 Books")
    tab1, tab2, tab3 = st.tabs(["📋 All Books", "➕ Add Book", "✏️ Edit / Delete"])

    # Tab 1 — show all books
    with tab1:
        books = pd.read_sql("SELECT * FROM books", con=con)
        books["is_available"] = books["is_available"].map({1: "✅ Available", 0: "❌ On Loan"})
        books.columns = ["Title", "Author", "Genre", "ISBN", "Status"]
        st.dataframe(books, use_container_width=True, hide_index=True, height=500)

    # Tab 2 — add a book
    with tab2:
        title  = st.text_input("Title *")
        ISBN   = st.text_input("ISBN *")
        author = st.text_input("Author (optional)")
        genre  = st.text_input("Genre (optional)")

        if st.button("➕ Add Book"):
            if not title or not ISBN:
                st.error("⚠️ Title and ISBN are required!")
            else:
                new = pd.DataFrame({
                    "title": [title], "author": [author or None],
                    "genre": [genre or None], "ISBN": [ISBN], "is_available": [1]
                })
                try:
                    new.to_sql("books", if_exists="append", con=con, index=False)
                    st.success(f"✅ '{title}' was successfully added to the library!")
                except Exception as e:
                    if "Duplicate entry" in str(e):
                        st.error(f"❌ A book with ISBN '{ISBN}' already exists!")
                    else:
                        raise

    # Tab 3 — edit or delete
    with tab3:
        books = pd.read_sql("SELECT * FROM books", con=con)
        if books.empty:
            st.info("No books yet.")
        else:
            labels = (books["title"] + " — " + books["ISBN"]).tolist()
            idx    = st.selectbox("Select a book:", range(len(labels)),
                                  format_func=lambda i: labels[i])
            row = books.iloc[idx]

            new_title  = st.text_input("Title",  value=row["title"],  key=f"bt{idx}")
            new_author = st.text_input("Author", value=row["author"] if pd.notna(row["author"]) else "", key=f"ba{idx}")
            new_genre  = st.text_input("Genre",  value=row["genre"]  if pd.notna(row["genre"])  else "", key=f"bg{idx}")

            col1, col2 = st.columns(2)
            if col1.button("💾 Save Changes"):
                run_query("UPDATE books SET title=:t, author=:a, genre=:g WHERE ISBN=:i",
                          {"t": new_title, "a": new_author or None,
                           "g": new_genre or None, "i": row["ISBN"]})
                st.success(f"✅ '{new_title}' updated!")

            if col2.button("🗑️ Delete", type="secondary"):
                run_query("DELETE FROM books WHERE ISBN=:i", {"i": row["ISBN"]})
                st.success(f"🗑️ '{row['title']}' deleted.")
                st.rerun()

# --------------------------------------------------------
# PAGE: FRIENDS
# --------------------------------------------------------
elif page == "👥 Friends":
    st.title("👥 Friends")
    tab1, tab2, tab3 = st.tabs(["📋 All Friends", "➕ Add Friend", "✏️ Edit / Delete"])

    # Tab 1 — show all friends
    with tab1:
        friends = pd.read_sql("SELECT * FROM friends", con=con)
        friends.columns = ["ID", "Name", "Phone Number", "Max Loans", "Notes"]
        st.dataframe(friends, use_container_width=True, hide_index=True, height=500)

    # Tab 2 — add a friend
    with tab2:
        name      = st.text_input("Name *")
        phone     = st.text_input("Phone number *")
        max_loans = st.number_input("Max loans allowed:", min_value=1, max_value=10, value=2)
        notes     = st.text_area("Notes (optional)")

        if st.button("➕ Add Friend"):
            if not name or not phone:
                st.error("⚠️ Name and phone number are required!")
            else:
                new = pd.DataFrame({
                    "name_": [name.strip()], "phone_number": [phone],
                    "max_loans": [max_loans], "notes": [notes or None]
                })
                new.to_sql("friends", if_exists="append", con=con, index=False)
                st.success(f"✅ '{name}' was successfully added!")

    # Tab 3 — edit or delete
    with tab3:
        friends = pd.read_sql("SELECT * FROM friends", con=con)
        if friends.empty:
            st.info("No friends yet.")
        else:
            labels = friends["name_"].tolist()
            idx    = st.selectbox("Select a friend:", range(len(labels)),
                                  format_func=lambda i: labels[i])
            row = friends.iloc[idx]

            new_name  = st.text_input("Name",         value=row["name_"],        key=f"fn{idx}")
            new_phone = st.text_input("Phone number", value=row["phone_number"], key=f"fp{idx}")
            new_max   = st.number_input("Max loans",  value=int(row["max_loans"]),
                                        min_value=1, max_value=10,               key=f"fm{idx}")
            new_notes = st.text_area("Notes", value=row["notes"] if pd.notna(row["notes"]) else "", key=f"fo{idx}")

            col1, col2 = st.columns(2)
            if col1.button("💾 Save Changes"):
                run_query("""UPDATE friends SET name_=:n, phone_number=:p,
                             max_loans=:m, notes=:o WHERE friend_id=:i""",
                          {"n": new_name, "p": new_phone,
                           "m": new_max,  "o": new_notes or None, "i": row["friend_id"]})
                st.success(f"✅ '{new_name}' updated!")

            if col2.button("🗑️ Delete", type="secondary"):
                run_query("DELETE FROM friends WHERE friend_id=:i", {"i": row["friend_id"]})
                st.success(f"🗑️ '{row['name_']}' deleted.")
                st.rerun()

# --------------------------------------------------------
# PAGE: LEND A BOOK
# --------------------------------------------------------
elif page == "📤 Lend a Book":
    st.title("📤 Lend a Book")

    books   = pd.read_sql("SELECT * FROM books WHERE is_available = 1", con=con)
    friends = pd.read_sql("SELECT * FROM friends", con=con)

    if books.empty:
        st.warning("⚠️ No books available to lend right now.")
    else:
        book_options   = dict(zip(books["title"],   books["ISBN"]))
        friend_options = dict(zip(friends["name_"], friends["friend_id"]))

        selected_book = st.selectbox("📖 Which book?", list(book_options.keys()))

        st.markdown("**👤 Who is borrowing it?**")
        mode = st.radio("", ["Select existing friend", "Type a new name"],
                        horizontal=True, label_visibility="collapsed")

        friend_id = None
        new_added = False

        if mode == "Select existing friend":
            if friends.empty:
                st.warning("No friends yet — use 'Type a new name'!")
            else:
                chosen    = st.selectbox("Select friend:", list(friend_options.keys()))
                friend_id = friend_options[chosen]
        else:
            new_name  = st.text_input("Name *")
            new_phone = st.text_input("Phone number (optional)")

        loan_date = st.date_input("📅 Loan date:", value=date.today())
        notes     = st.text_input("📝 Notes (optional):")

        if st.button("📤 Lend Book"):
            # If typing a new name, add them to friends first
            if mode == "Type a new name":
                if not new_name:
                    st.error("⚠️ Please enter a name!")
                    st.stop()
                # Check if they already exist
                existing = pd.read_sql(
                    f"SELECT * FROM friends WHERE LOWER(name_) = '{new_name.strip().lower()}'", con=con)
                if not existing.empty:
                    friend_id = existing.iloc[0]["friend_id"]
                else:
                    new = pd.DataFrame({
                        "name_": [new_name.strip()],
                        "phone_number": [new_phone or "not provided"],
                        "max_loans": [2], "notes": [None]
                    })
                    new.to_sql("friends", if_exists="append", con=con, index=False)
                    new_added = True
                    result    = pd.read_sql(
                        f"SELECT * FROM friends WHERE LOWER(name_) = '{new_name.strip().lower()}'", con=con)
                    friend_id = result.iloc[0]["friend_id"]

            if friend_id is not None:
                run_query("""INSERT INTO loans (book_id, friend_id, loan_date, return_date, notes)
                             VALUES (:b, :f, :d, NULL, :n)""",
                          {"b": book_options[selected_book], "f": friend_id,
                           "d": loan_date, "n": notes or None})
                run_query("UPDATE books SET is_available=0 WHERE ISBN=:i",
                          {"i": book_options[selected_book]})
                if new_added:
                    st.info(f"👤 '{new_name}' was new — added to friends automatically!")
                borrower = new_name if mode == "Type a new name" else chosen
                st.success(f"✅ '{selected_book}' successfully lent to {borrower}!")

# --------------------------------------------------------
# PAGE: RETURN A BOOK
# --------------------------------------------------------
elif page == "📥 Return a Book":
    st.title("📥 Return a Book")

    active = pd.read_sql("""
        SELECT l.loan_id, b.title AS Book, b.ISBN,
               f.name_ AS "Borrowed By", f.phone_number AS Contact, l.loan_date AS Since
        FROM loans l
        JOIN books b ON l.book_id = b.ISBN
        JOIN friends f ON l.friend_id = f.friend_id
        WHERE l.return_date IS NULL
    """, con=con)

    if active.empty:
        st.success("🎉 All books have been returned!")
    else:
        st.dataframe(active[["Book", "Borrowed By", "Contact", "Since"]],
                     use_container_width=True, hide_index=True)
        st.markdown("---")

        options = {
            f"{r['Book']} → {r['Borrowed By']}": (r["loan_id"], r["ISBN"])
            for _, r in active.iterrows()
        }
        selected    = st.selectbox("Which book is being returned?", list(options.keys()))
        return_date = st.date_input("📅 Return date:", value=date.today())

        if st.button("📥 Mark as Returned"):
            loan_id, isbn = options[selected]
            run_query("UPDATE loans SET return_date=:d WHERE loan_id=:i",
                      {"d": return_date, "i": loan_id})
            run_query("UPDATE books SET is_available=1 WHERE ISBN=:i", {"i": isbn})
            st.success(f"✅ '{selected.split(' → ')[0]}' successfully returned!")
            st.rerun()

# --------------------------------------------------------
# PAGE: ALL LOANS
# --------------------------------------------------------
elif page == "📋 All Loans":
    st.title("📋 All Loans")

    loans = pd.read_sql("""
        SELECT b.title AS Book, f.name_ AS "Borrowed By",
               l.loan_date AS "Date Borrowed",
               l.return_date AS "Date Returned",
               l.notes AS Notes
        FROM loans l
        JOIN books b ON l.book_id = b.ISBN
        JOIN friends f ON l.friend_id = f.friend_id
    """, con=con)

    loans["Date Returned"] = loans["Date Returned"].fillna("❌ Not returned yet")
    st.dataframe(loans, use_container_width=True, hide_index=True, height=500)
