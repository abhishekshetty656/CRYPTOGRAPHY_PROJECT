from flask import Flask, render_template, request, session, redirect, url_for
from utils.otp import generate_otp, send_otp_email
from config import SECRET_KEY

app = Flask(__name__)
app.secret_key = SECRET_KEY

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        otp = generate_otp()

        session["otp"] = otp
        session["email"] = email

        send_otp_email(email, otp)

        return redirect(url_for("verify_otp"))

    return render_template("login.html")

@app.route("/verify", methods=["GET", "POST"])
def verify_otp():
    if request.method == "POST":
        user_otp = request.form["otp"]

        if user_otp == session.get("otp"):
            session.pop("otp", None)
            return redirect(url_for("success"))
        else:
            return "Invalid OTP. Try again."

    return render_template("verify_otp.html")

@app.route("/success")
def success():
    return render_template("success.html")

if __name__ == "__main__":
    app.run(debug=True)
