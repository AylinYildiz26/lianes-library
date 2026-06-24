import os
import streamlit as st
import mysql.connector
import pandas as pd
from datetime import date

# --------------------------------------------------------
# DATABASE CONNECTION
# --------------------------------------------------------

def get_connection():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password=os.environ.get("DB_PASSWORD"),
        database="sample_library"
    )
    return conn

# --------------------------------------------------------
# CRUD FUNCTIONS
# --------------------------------------------------------

def get_all_books():
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM books", conn)
    conn.close()
    return df

def get_all_friends():
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM friends", conn)
    conn.close()
    return df

def get_active_loans():
    conn = get_connection()
    query = """
        SELECT 
            l.loan_id,
            b.title          AS book_title,
            f.name_          AS borrowed_by,
            f.phone_number   AS contact,
            l.loan_date,
            l.return_date
        FROM loans l
        JOIN books   b ON l.book_id   = b.ISBN
        JOIN friends f ON l.friend_id = f.friend_id
        WHERE l.return_date IS NULL
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def get_all_loans():
    conn = get_connection()
    query = """
        SELECT 
            l.loan_id,
            b.title          AS book_title,
            f.name_          AS borrowed_by,
            l.loan_date,
            l.return_date,
            l.notes
        FROM loans l
        JOIN books   b ON l.book_id   = b.ISBN
        JOIN friends f ON l.friend_id = f.friend_id
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def add_book(title, ISBN, author=None, genre=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO books (title, author, genre, ISBN, is_available)
        VALUES (%s, %s, %s, %s, 1)
    """, (title, author, genre, ISBN))
    conn.commit()
    cursor.close()
    conn.close()

def add_friend(name, phone_number, max_loans=2, notes=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO friends (name_, phone_number, max_loans, notes)
        VALUES (%s, %s, %s, %s)
    """, (name.strip(), phone_number, max_loans, notes))
    conn.commit()
    cursor.close()
    conn.close()

def lend_book(ISBN, friend_id, loan_date, notes=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO loans (book_id, friend_id, loan_date, return_date, notes)
        VALUES (%s, %s, %s, NULL, %s)
    """, (ISBN, friend_id, loan_date, notes))
    cursor.execute("UPDATE books SET is_available = 0 WHERE ISBN = %s", (ISBN,))
    conn.commit()
    cursor.close()
    conn.close()

def return_book(loan_id, ISBN, return_date):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE loans SET return_date = %s WHERE loan_id = %s
    """, (return_date, loan_id))
    cursor.execute("UPDATE books SET is_available = 1 WHERE ISBN = %s", (ISBN,))
    conn.commit()
    cursor.close()
    conn.close()

# --------------------------------------------------------
# STREAMLIT APP
# --------------------------------------------------------

st.set_page_config(page_title="📚 Liane's Library", layout="wide")
st.title("📚 Liane's Library")

# Sidebar navigation
page = st.sidebar.selectbox("Navigation", [
    "📖 All Books",
    "👥 Friends",
    "📤 Lend a Book",
    "📥 Return a Book",
    "➕ Add Book",
    "➕ Add Friend",
    "📋 All Loans"
])

# --------------------------------------------------------
# PAGE: All Books
# --------------------------------------------------------
if page == "📖 All Books":
    st.header("📖 All Books")
    df = get_all_books()
    df["is_available"] = df["is_available"].map({1: "✅ Available", 0: "❌ On Loan"})
    st.dataframe(df, use_container_width=True)

# --------------------------------------------------------
# PAGE: Friends
# --------------------------------------------------------
elif page == "👥 Friends":
    st.header("👥 Friends")
    df = get_all_friends()
    st.dataframe(df, use_container_width=True)

# --------------------------------------------------------
# PAGE: Lend a Book
# --------------------------------------------------------
elif page == "📤 Lend a Book":
    st.header("📤 Lend a Book")

    # Only show available books
    books_df = get_all_books()
    available_books = books_df[books_df["is_available"] == 1]
    friends_df = get_all_friends()

    if available_books.empty:
        st.warning("No books available to lend right now.")
    else:
        book_options = dict(zip(available_books["title"], available_books["ISBN"]))
        friend_options = dict(zip(friends_df["name_"], friends_df["friend_id"]))

        selected_book = st.selectbox("Select a book:", list(book_options.keys()))
        selected_friend = st.selectbox("Select a friend:", list(friend_options.keys()))
        loan_date = st.date_input("Loan date:", value=date.today())
        notes = st.text_input("Notes (optional):")

        if st.button("📤 Lend Book"):
            lend_book(
                ISBN=book_options[selected_book],
                friend_id=friend_options[selected_friend],
                loan_date=loan_date,
                notes=notes if notes else None
            )
            st.success(f"✅ '{selected_book}' lent to {selected_friend}!")
            st.rerun()

# --------------------------------------------------------
# PAGE: Return a Book
# --------------------------------------------------------
elif page == "📥 Return a Book":
    st.header("📥 Return a Book")

    active_loans = get_active_loans()

    if active_loans.empty:
        st.success("🎉 All books have been returned!")
    else:
        st.dataframe(active_loans, use_container_width=True)

        loan_options = {
            f"{row['book_title']} → {row['borrowed_by']}": row['loan_id']
            for _, row in active_loans.iterrows()
        }

        selected_loan = st.selectbox("Select loan to return:", list(loan_options.keys()))
        return_date = st.date_input("Return date:", value=date.today())

        # Get ISBN for selected loan
        selected_title = selected_loan.split(" → ")[0]
        books_df = get_all_books()
        isbn = books_df[books_df["title"] == selected_title]["ISBN"].values[0]

        if st.button("📥 Mark as Returned"):
            return_book(
                loan_id=loan_options[selected_loan],
                ISBN=isbn,
                return_date=return_date
            )
            st.success(f"✅ '{selected_title}' marked as returned!")
            st.rerun()

# --------------------------------------------------------
# PAGE: Add Book
# --------------------------------------------------------
elif page == "➕ Add Book":
    st.header("➕ Add a New Book")

    title = st.text_input("Title *")
    ISBN = st.text_input("ISBN *")
    author = st.text_input("Author (optional)")
    genre = st.text_input("Genre (optional)")

    if st.button("➕ Add Book"):
        if not title or not ISBN:
            st.error("Title and ISBN are required!")
        else:
            add_book(
                title=title,
                ISBN=ISBN,
                author=author if author else None,
                genre=genre if genre else None
            )
            st.success(f"✅ '{title}' added to the library!")
            st.rerun()

# --------------------------------------------------------
# PAGE: Add Friend
# --------------------------------------------------------
elif page == "➕ Add Friend":
    st.header("➕ Add a New Friend")

    name = st.text_input("Name *")
    phone = st.text_input("Phone number *")
    max_loans = st.number_input("Max loans allowed:", min_value=1, max_value=10, value=2)
    notes = st.text_area("Notes (optional)")

    if st.button("➕ Add Friend"):
        if not name or not phone:
            st.error("Name and phone number are required!")
        else:
            add_friend(
                name=name,
                phone_number=phone,
                max_loans=max_loans,
                notes=notes if notes else None
            )
            st.success(f"✅ '{name}' added!")
            st.rerun()

# --------------------------------------------------------
# PAGE: All Loans
# --------------------------------------------------------
elif page == "📋 All Loans":
    st.header("📋 All Loans")
    df = get_all_loans()
    df["return_date"] = df["return_date"].fillna("❌ Not returned yet")
    st.dataframe(df, use_container_width=True)
