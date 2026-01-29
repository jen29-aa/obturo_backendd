"""
Email service for sending booking confirmation emails
"""
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings


def send_booking_confirmation_email(user, booking, station):
    """
    Send booking confirmation email to user
    
    Args:
        user: User object
        booking: Booking object
        station: ChargingStation object
    """
    try:
        subject = f"⚡ Booking Confirmation - {station.name}"
        
        # Email content
        context = {
            'user_name': user.first_name or user.username,
            'station_name': station.name,
            'station_address': station.address,
            'booking_id': booking.id,
            'start_time': booking.start_time.strftime('%B %d, %Y at %I:%M %p'),
            'end_time': booking.end_time.strftime('%B %d, %Y at %I:%M %p'),
            'charger_type': station.charger_type,
            'connector_type': station.connector_type,
            'power_kw': station.power_kw,
            'price_per_kwh': station.price_per_kwh,
        }
        
        html_message = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px; background: #f9f9f9; border-radius: 8px;">
                    <div style="text-align: center; margin-bottom: 30px;">
                        <h1 style="color: #0052cc; margin: 0;">⚡ Obturo</h1>
                        <p style="color: #666; margin: 10px 0 0 0;">Your EV Charging Booking Confirmation</p>
                    </div>
                    
                    <div style="background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                        <h2 style="color: #0052cc; border-bottom: 2px solid #0052cc; padding-bottom: 10px;">Booking Confirmed!</h2>
                        
                        <p style="margin-top: 20px;">Hi {context['user_name']},</p>
                        <p>Your charging station booking has been confirmed. Here are your booking details:</p>
                        
                        <div style="background: #f0f0f0; padding: 20px; border-radius: 8px; margin: 20px 0;">
                            <h3 style="margin-top: 0; color: #0052cc;">Booking Details</h3>
                            <p><strong>Booking ID:</strong> #{context['booking_id']}</p>
                            <p><strong>Station:</strong> {context['station_name']}</p>
                            <p><strong>Address:</strong> {context['station_address']}</p>
                            <p><strong>Check-in:</strong> {context['start_time']}</p>
                            <p><strong>Check-out:</strong> {context['end_time']}</p>
                            
                            <h3 style="color: #0052cc;">Station Specifications</h3>
                            <p><strong>Charger Type:</strong> {context['charger_type']}</p>
                            <p><strong>Connector:</strong> {context['connector_type']}</p>
                            <p><strong>Power:</strong> {context['power_kw']} kW</p>
                            <p><strong>Price:</strong> ₹{context['price_per_kwh']}/kWh</p>
                        </div>
                        
                        <div style="background: #e3f2fd; padding: 15px; border-left: 4px solid #0052cc; margin: 20px 0; border-radius: 4px;">
                            <strong>📍 Important:</strong> Please arrive 10 minutes before your scheduled check-in time. If you need to cancel or modify your booking, please do so at least 2 hours before your check-in time.
                        </div>
                        
                        <p style="margin-top: 30px; text-align: center;">
                            <a href="http://127.0.0.1:8000/bookings/" style="display: inline-block; padding: 12px 30px; background: #0052cc; color: white; text-decoration: none; border-radius: 6px;">View Your Bookings</a>
                        </p>
                    </div>
                    
                    <div style="text-align: center; margin-top: 30px; color: #999; font-size: 12px;">
                        <p>This is an automated message. Please do not reply to this email.</p>
                        <p>&copy; 2026 Obturo. All rights reserved.</p>
                    </div>
                </div>
            </body>
        </html>
        """
        
        plain_message = f"""
Booking Confirmation
Hi {context['user_name']},

Your charging station booking has been confirmed.

Booking Details:
- Booking ID: #{context['booking_id']}
- Station: {context['station_name']}
- Address: {context['station_address']}
- Check-in: {context['start_time']}
- Check-out: {context['end_time']}

Station Specifications:
- Charger Type: {context['charger_type']}
- Connector: {context['connector_type']}
- Power: {context['power_kw']} kW
- Price: ₹{context['price_per_kwh']}/kWh

Please arrive 10 minutes before your scheduled check-in time.

Thank you for using Obturo!
        """
        
        # Send email (only plain text for console backend to avoid clutter)
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=None if settings.EMAIL_BACKEND == 'django.core.mail.backends.console.EmailBackend' else html_message,
            fail_silently=False,
        )
        
        print(f"✅ Booking confirmation email sent to {user.email}")
        
        return True
    except Exception as e:
        print(f"Error sending booking confirmation email: {e}")
        return False


def send_waitlist_notification_email(user, station, position):
    """
    Send waitlist notification email to user
    
    Args:
        user: User object
        station: ChargingStation object
        position: Waitlist position
    """
    try:
        subject = f"⏳ You've Been Added to Waitlist - {station.name}"
        
        context = {
            'user_name': user.first_name or user.username,
            'station_name': station.name,
            'station_address': station.address,
            'position': position,
            'charger_type': station.charger_type,
        }
        
        html_message = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #ff9800;">⏳ Added to Waitlist</h2>
                    <p>Hi {context['user_name']},</p>
                    <p>The station <strong>{context['station_name']}</strong> is currently full. You have been added to the waitlist at <strong>position {context['position']}</strong>.</p>
                    <p>We will notify you via push notification when a slot becomes available.</p>
                </div>
            </body>
        </html>
        """
        
        plain_message = f"""
You've been added to the waitlist for {context['station_name']}
Position: {context['position']}

We will notify you when a slot becomes available.
        """
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        return True
    except Exception as e:
        print(f"Error sending waitlist notification email: {e}")
        return False
