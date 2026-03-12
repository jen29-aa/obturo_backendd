# 💳 Payment Integration Guide for Obturo

## **Quick Summary**
Currently, users can book stations but **there's no payment gateway**. This means bookings are created without actual payment.

---

## **Option 1: Razorpay (RECOMMENDED FOR INDIA)**

### **Setup Steps:**

1. **Install Razorpay SDK**
```bash
pip install razorpay
```

2. **Create Payment View** (`stations/views.py`):
```python
import razorpay
from django.conf import settings

client = razorpay.Client(
    auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_payment_order(request):
    booking_id = request.data.get('booking_id')
    booking = Booking.objects.get(id=booking_id, user=request.user)
    
    # Calculate cost (price_per_kwh * duration_hours * power_kw)
    cost_in_paise = int(booking.total_cost * 100)  # Razorpay uses paise
    
    order = client.order.create(
        amount=cost_in_paise,
        currency='INR',
        payment_capture='1',
        notes={
            'booking_id': booking.id,
            'station_name': booking.station.name
        }
    )
    
    return Response({
        'order_id': order['id'],
        'amount': order['amount'],
        'currency': order['currency'],
        'key': settings.RAZORPAY_KEY_ID
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_payment(request):
    payment_id = request.data.get('razorpay_payment_id')
    order_id = request.data.get('razorpay_order_id')
    signature = request.data.get('razorpay_signature')
    
    # Verify signature
    try:
        client.utility.verify_payment_signature({
            'razorpay_order_id': order_id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature': signature
        })
        
        # Mark booking as paid
        booking = Booking.objects.get(razorpay_order_id=order_id)
        booking.is_paid = True
        booking.payment_id = payment_id
        booking.save()
        
        return Response({'status': 'Payment verified'})
    except:
        return Response({'error': 'Payment verification failed'}, status=400)
```

3. **Add to settings.py**:
```python
RAZORPAY_KEY_ID = 'your_key_id'
RAZORPAY_KEY_SECRET = 'your_key_secret'
```

4. **Frontend Integration** (`station_detail.html`):
```javascript
async function processPayment(bookingId) {
    try {
        // Create order
        const orderRes = await fetch('/api/create-payment-order/', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${AUTH_TOKEN}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ booking_id: bookingId })
        });
        
        const orderData = await orderRes.json();
        
        // Open Razorpay
        const options = {
            key: orderData.key,
            amount: orderData.amount,
            currency: orderData.currency,
            name: 'Obturo',
            description: 'EV Charging Booking',
            order_id: orderData.order_id,
            handler: function(response) {
                verifyPayment(response);
            }
        };
        
        const rzp = new Razorpay(options);
        rzp.open();
    } catch (error) {
        console.error('Payment error:', error);
    }
}

function verifyPayment(response) {
    fetch('/api/verify-payment/', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${AUTH_TOKEN}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            razorpay_payment_id: response.razorpay_payment_id,
            razorpay_order_id: response.razorpay_order_id,
            razorpay_signature: response.razorpay_signature
        })
    })
    .then(res => res.json())
    .then(data => {
        alert('Payment successful!');
        window.location.href = '/bookings/';
    })
    .catch(err => alert('Payment verification failed'));
}
```

---

## **Option 2: Stripe (INTERNATIONAL)**

### **Setup Steps:**

1. **Install Stripe**
```bash
pip install stripe
```

2. **Create Intent View**:
```python
import stripe
from django.conf import settings

stripe.api_key = settings.STRIPE_SECRET_KEY

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_payment_intent(request):
    booking_id = request.data.get('booking_id')
    booking = Booking.objects.get(id=booking_id, user=request.user)
    
    intent = stripe.PaymentIntent.create(
        amount=int(booking.total_cost * 100),  # cents
        currency='inr',
        metadata={'booking_id': booking.id}
    )
    
    return Response({'clientSecret': intent.client_secret})
```

---

## **Required Model Updates**

Add to `stations/models.py`:

```python
class Booking(models.Model):
    # ... existing fields ...
    
    # Payment fields
    is_paid = models.BooleanField(default=False)
    total_cost = models.FloatField(default=0)
    payment_id = models.CharField(max_length=255, null=True, blank=True)
    razorpay_order_id = models.CharField(max_length=255, null=True, blank=True)
    payment_date = models.DateTimeField(null=True, blank=True)
    payment_method = models.CharField(max_length=50, null=True, blank=True)  # 'razorpay', 'stripe', etc.
    
    def calculate_cost(self):
        """Calculate booking cost based on duration and station pricing"""
        duration_hours = (self.end_time - self.start_time).total_seconds() / 3600
        power_kw = self.station.power_kw
        price_per_kwh = self.station.price_per_kwh
        
        energy_consumed = power_kw * duration_hours
        self.total_cost = energy_consumed * price_per_kwh
        self.save()
        return self.total_cost
```

---

## **Modified Booking Creation Flow**

```python
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_booking(request):
    station_id = request.data.get('station_id')
    start_time = request.data.get('start_time')
    end_time = request.data.get('end_time')
    
    station = ChargingStation.objects.get(id=station_id)
    
    # Create booking but mark as unpaid
    booking = Booking.objects.create(
        user=request.user,
        station=station,
        start_time=start_time,
        end_time=end_time,
        status='pending_payment'  # Not 'active' yet
    )
    
    # Calculate cost
    booking.calculate_cost()
    
    # Return booking details + request payment
    return Response({
        'booking_id': booking.id,
        'total_cost': booking.total_cost,
        'status': 'pending_payment'
    })
```

---

## **Refund System**

```python
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def refund_booking(request):
    booking_id = request.data.get('booking_id')
    booking = Booking.objects.get(id=booking_id, user=request.user)
    
    # Check if within cancellation window
    time_until_booking = booking.start_time - timezone.now()
    
    if time_until_booking.total_seconds() < 30 * 60:  # Less than 30 mins
        return Response({
            'error': 'Cannot cancel within 30 minutes of booking'
        }, status=400)
    
    # Process refund
    if booking.payment_id:
        if booking.payment_method == 'razorpay':
            refund = client.payment.refund(booking.payment_id)
        elif booking.payment_method == 'stripe':
            stripe.Refund.create(
                payment_intent=booking.payment_id
            )
    
    # Update booking
    booking.status = 'cancelled'
    booking.refund_date = timezone.now()
    booking.save()
    
    return Response({'status': 'Refund processed'})
```

---

## **Priority Implementation**
1. ✅ Add payment fields to Booking model
2. ✅ Create payment endpoint (Razorpay recommended for India)
3. ✅ Add payment verification
4. ✅ Update booking creation to handle unpaid status
5. ✅ Add refund system
6. ✅ Update frontend to show payment status
7. ✅ Send payment confirmation email

---

**Timeline:** 2-3 days for full integration
**Cost:** Free (Razorpay charges on transaction)
**Next Step:** Choose Razorpay or Stripe and start integration
