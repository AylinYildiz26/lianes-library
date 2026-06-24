import os
import mysql.connector
import pandas as pd

# --------------------------------------------------------
# DATABASE CONNECTION
# Credentials are read from environment variables.
# Copy .env.example to .env and set your own values.
# --------------------------------------------------------

def get_connection():
    """Create and return a connection to the database."""
    conn = mysql.connector.connect(
        host=os.environ.get("DB_HOST", "localhost"),
        user=os.environ.get("DB_USER", "root"),
        password=os.environ.get("DB_PASSWORD"),
        database=os.environ.get("DB_NAME", "sample_library"),
    )
    return conn


# --------------------------------------------------------
# BOOKS — CRUD
# --------------------------------------------------------

# CREATE
def add_book(title, ISBN, author=None, genre=None):
    """Add a new book to the library."""
    conn = get_connection()
    cursor = conn.cursor()
    query = """
        INSERT INTO books (title, author, genre, ISBN, is_available)
        VALUES (%s, %s, %s, %s, 1)
    """
    cursor.execute(query, (title, author, genre, ISBN))
    conn.commit()
    cursor.close()
    conn.close()
    print(f"✅ Book '{title}' added successfully.")


# READ — all books
def get_all_books():
    """Return all books as a DataFrame."""
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM books", conn)
    conn.close()
    return df


# READ — only available books
def get_available_books():
    """Return only books that are currently available."""
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM books WHERE is_available = 1", conn)
    conn.close()
    return df


# READ — only books currently on loan
def get_loaned_books():
    """Return only books that are currently on loan."""
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM books WHERE is_available = 0", conn)
    conn.close()
    return df


# UPDATE
def update_book(ISBN, title=None, author=None, genre=None):
    """Update book details by ISBN."""
    conn = get_connection()
    cursor = conn.cursor()
    if title:
        cursor.execute("UPDATE books SET title = %s WHERE ISBN = %s", (title, ISBN))
    if author:
        cursor.execute("UPDATE books SET author = %s WHERE ISBN = %s", (author, ISBN))
    if genre:
        cursor.execute("UPDATE books SET genre = %s WHERE ISBN = %s", (genre, ISBN))
    conn.commit()
    cursor.close()
    conn.close()
    print(f"✅ Book with ISBN '{ISBN}' updated.")


# DELETE
def delete_book(ISBN):
    """Delete a book by ISBN."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM books WHERE ISBN = %s", (ISBN,))
    conn.commit()
    cursor.close()
    conn.close()
    print(f"🗑️ Book with ISBN '{ISBN}' deleted.")


# --------------------------------------------------------
# FRIENDS — CRUD
# --------------------------------------------------------

# CREATE
def add_friend(name, phone_number, max_loans=2, notes=None):
    """Add a new friend/borrower."""
    conn = get_connection()
    cursor = conn.cursor()
    query = """
        INSERT INTO friends (name_, phone_number, max_loans, notes)
        VALUES (%s, %s, %s, %s)
    """
    cursor.execute(query, (name.strip(), phone_number, max_loans, notes))
    conn.commit()
    cursor.close()
    conn.close()
    print(f"✅ Friend '{name}' added successfully.")


# READ
def get_all_friends():
    """Return all friends as a DataFrame."""
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM friends", conn)
    conn.close()
    return df


# UPDATE
def update_friend(friend_id, phone_number=None, max_loans=None, notes=None):
    """Update friend details by friend_id."""
    conn = get_connection()
    cursor = conn.cursor()
    if phone_number:
        cursor.execute("UPDATE friends SET phone_number = %s WHERE friend_id = %s", (phone_number, friend_id))
    if max_loans is not None:
        cursor.execute("UPDATE friends SET max_loans = %s WHERE friend_id = %s", (max_loans, friend_id))
    if notes:
        cursor.execute("UPDATE friends SET notes = %s WHERE friend_id = %s", (notes, friend_id))
    conn.commit()
    cursor.close()
    conn.close()
    print(f"✅ Friend with ID '{friend_id}' updated.")


# DELETE
def delete_friend(friend_id):
    """Delete a friend by friend_id."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM friends WHERE friend_id = %s", (friend_id,))
    conn.commit()
    cursor.close()
    conn.close()
    print(f"🗑️ Friend with ID '{friend_id}' deleted.")


# --------------------------------------------------------
# LOANS — CRUD
# --------------------------------------------------------

# CREATE — lend a book
def lend_book(ISBN, friend_id, loan_date, notes=None):
    """Record a new loan and mark book as unavailable."""
    conn = get_connection()
    cursor = conn.cursor()

    # Insert new loan
    query = """
        INSERT INTO loans (book_id, friend_id, loan_date, return_date, notes)
        VALUES (%s, %s, %s, NULL, %s)
    """
    cursor.execute(query, (ISBN, friend_id, loan_date, notes))

    # Mark book as unavailable
    cursor.execute("UPDATE books SET is_available = 0 WHERE ISBN = %s", (ISBN,))

    conn.commit()
    cursor.close()
    conn.close()
    print(f"📤 Book '{ISBN}' lent to friend ID '{friend_id}' on {loan_date}.")


# READ — all loans
def get_all_loans():
    """Return all loans with book and friend details as a DataFrame."""
    conn = get_connection()
    query = """
        SELECT 
            l.loan_id,
            b.title          AS book_title,
            b.ISBN,
            f.name_          AS borrowed_by,
            f.phone_number   AS contact,
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


# READ — only active loans (not yet returned)
def get_active_loans():
    """Return all loans where the book has not been returned yet."""
    conn = get_connection()
    query = """
        SELECT 
            b.title          AS book_title,
            b.ISBN,
            f.name_          AS borrowed_by,
            f.phone_number   AS contact,
            l.loan_date,
            l.notes
        FROM loans l
        JOIN books   b ON l.book_id   = b.ISBN
        JOIN friends f ON l.friend_id = f.friend_id
        WHERE l.return_date IS NULL
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df


# UPDATE — return a book
def return_book(ISBN, friend_id, return_date):
    """Mark a book as returned and set it back to available."""
    conn = get_connection()
    cursor = conn.cursor()

    # Set return date in loans
    query = """
        UPDATE loans
        SET return_date = %s
        WHERE book_id = %s AND friend_id = %s AND return_date IS NULL
    """
    cursor.execute(query, (return_date, ISBN, friend_id))

    # Mark book as available again
    cursor.execute("UPDATE books SET is_available = 1 WHERE ISBN = %s", (ISBN,))

    conn.commit()
    cursor.close()
    conn.close()
    print(f"📥 Book '{ISBN}' returned on {return_date}.")


# DELETE — remove a loan record
def delete_loan(loan_id):
    """Delete a loan record by loan_id."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM loans WHERE loan_id = %s", (loan_id,))
    conn.commit()
    cursor.close()
    conn.close()
    print(f"🗑️ Loan ID '{loan_id}' deleted.")


# --------------------------------------------------------
# QUICK TEST — run this file directly to check everything
# --------------------------------------------------------
if __name__ == "__main__":
    print("📚 All Books:")
    print(get_all_books())

    print("\n📋 Active Loans:")
    print(get_active_loans())

    print("\n👥 All Friends:")
    print(get_all_friends())
