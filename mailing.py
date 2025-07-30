from email.message import EmailMessage
import ssl
import smtplib


def send_verification(email,code):
        email_from = "adi.profile1@gmail.com"
        email_password="gwaryitmlyzygepr"
        email_to=email

        subject="herring: Verify to start playing!"

        body = f""" <!DOCTYPE html>
<html>
<head>
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Marcellus&display=swap');



</style>

</head>
    <body style="color:white;background-color:black;
font-family: 'Marcellus', serif;
text-align:center;
">
    <div>
    
    </div>
    <h1 style="color:#c91a1a;
font-family: 'DM Serif Display', serif;
text-align:center;
font-size:70px;">
        herring
    </h1>    
    
    <h2 "color:white;"> <strong> Finish Creating your account! </strong></h2>
        
    <h2 style="color:white;">    
        Here's your verification code
    </h2>
    <h1 style="color:white;">
        {code}
    </h1>
    </body>
    </html>
        """

        em=EmailMessage()
        em["From"]= email_from
        em['To']=email_to
        em["Subject"]=subject
        em.set_content(body,subtype="html")
        context = ssl.create_default_context()

        with smtplib.SMTP_SSL('smtp.gmail.com',465,context=context) as smtp:
            smtp.login(email_from,email_password)
            smtp.sendmail(email_from,email_to,em.as_string())


def send_forgot_password(email, code):
        email_from = "adi.profile1@gmail.com"
        email_password = "gwaryitmlyzygepr"
        email_to = email

        subject = "herring: Change your Password"

        body = f""" <!DOCTYPE html>
<html>
<head>
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Marcellus&display=swap');


</style>

</head>

    <body style="color:white;background-color:black;
font-family: 'Marcellus', serif;
text-align:center;">

    <h1 style="color:#c91a1a;
font-family: 'DM Serif Display', serif;
text-align:center;
font-size:70px;">
        herring
    </h1>    
    <h2 "color:white;"> <strong> Change your Password </strong></h2>

    <h2 style="color:white;">    
        Here's your verification code to change your password
    </h2>
    <h1 style="color:white;">
        {code}
    </h1>
    </body>
    </html>
        """

        em = EmailMessage()
        em["From"] = email_from
        em['To'] = email_to
        em["Subject"] = subject
        em.set_content(body, subtype="html")
        context = ssl.create_default_context()

        with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
                smtp.login(email_from, email_password)
                smtp.sendmail(email_from, email_to, em.as_string())



