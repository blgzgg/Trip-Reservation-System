import os
from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import string

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

base_dir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(base_dir, 'dbs', 'reservations.db')

def get_cost_matrix():
    cost_matrix = [[100, 75, 50, 100] for row in range(12)]
    return cost_matrix

def calculate_total_sales():
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT seatRow, seatColumn FROM reservations")
    reserved_seats = c.fetchall()
    cost_matrix = get_cost_matrix()
    total_sales = 0
    for seat in reserved_seats:
        row = seat[0]
        column = seat[1]
        total_sales += cost_matrix[row][column]
    conn.close()
    return total_sales

def get_reserved_seats():
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT seatRow, seatColumn FROM reservations")
    reserved_seats = c.fetchall()
    conn.close()
    return reserved_seats

# Generate new eTicketNumbers
def generate_eTicketNumber(first_name):
    target_string = 'INFOTC4320'
    result = ''
    target_index = 0

    for letter in first_name:
        result += target_string[target_index] + letter
        target_index += 1

    result += target_string[target_index:]

    return result

@app.route('/')
def main_menu():
    return render_template('index.html')

@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("SELECT * FROM admins WHERE username=? AND password=?", (username, password))
        admin = c.fetchone()
        conn.close()
        if admin:
            total_sales = calculate_total_sales()
            return render_template('admin_dashboard.html', total_sales=total_sales, cost_matrix=get_cost_matrix(), reserved_seats=get_reserved_seats())
        else:
            return render_template('admin_login.html', message="Invalid username or password. Please try again.")
    return render_template('admin_login.html')

@app.route('/reserve-seat', methods=['GET', 'POST'])
def reserve_seat():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']

        # Fixes the numbers in the seating chart
        seat_row = int(request.form['seat_row']) - 1
        seat_column = int(request.form['seat_column']) - 1
        
        # Check if seat is already reserved
        reserved_seats = get_reserved_seats()
        if (seat_row, seat_column) in reserved_seats:
            error = "Seat is already reserved. Please select another seat."
            return render_template('reserve_seat.html', cost_matrix=get_cost_matrix(), reserved_seats=reserved_seats, error=error)
        
        # If seat not reserved, proceed with reservation
        eTicketNumber = generate_eTicketNumber(first_name)
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("INSERT INTO reservations (passengerName, seatRow, seatColumn, eTicketNumber) VALUES (?, ?, ?, ?)", (first_name + " " + last_name, seat_row, seat_column, eTicketNumber))
        conn.commit()
        conn.close()
        
        # Redirect to reservation confirmation page
        return redirect(url_for('reserve_confirmation', first_name=first_name, last_name=last_name, eTicketNumber=eTicketNumber))
    
    return render_template('reserve_seat.html', cost_matrix=get_cost_matrix(), reserved_seats=get_reserved_seats())

@app.route('/reserve-confirmation/<first_name>/<last_name>/<eTicketNumber>')
def reserve_confirmation(first_name, last_name, eTicketNumber):
    return render_template('reserve_confirmation.html', first_name=first_name, last_name=last_name, eTicketNumber=eTicketNumber)


if __name__ == '__main__':
    app.run(debug=True)
