from django.core.mail import EmailMessage

def send_verification_email(user, verification):
    # Send verification email
    mail_subject = 'Your Hotel Reservation Account Verification Code'
    message = f"""
            Dear {user.name},

            Thank you for registering with our hotel reservation service. 
            Please use the following verification code to activate your account:

            Verification Code: {verification.code}

            This code will expire in 24 hours.

            If you didn't request this, please ignore this email.

            Best regards,
            Hotel Reservation Team
            """
    email = EmailMessage(mail_subject, message, to=[user.email])
    email.send()