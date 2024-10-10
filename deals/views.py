from django.contrib.auth import logout
from .models import Deal, Comment
import random
import datetime
from django.utils import timezone
from django.core.mail import send_mail
from django.shortcuts import render, redirect, get_object_or_404, HttpResponse
from django.contrib.auth.models import User, auth
from django.contrib import messages
import re
import logging
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login as auth_login, authenticate, logout
from .form import CommentForm
from django.http import HttpResponseForbidden, JsonResponse
import hashlib
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.conf import settings
import requests
from datetime import datetime, timedelta
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
import hmac
import json
import http.client
from twilio.rest import Client
from django.views.decorators.cache import never_cache, cache_control
from .forms import AddressForm


logger = logging.getLogger(__name__)


def index(request):
    return render(request, 'index.html')


def generate_otp():
    return str(random.randint(100000, 999999))


def signup(request):
    if request.method == 'POST':
        if 'otp' in request.POST:  # Check if OTP is being submitted
            otp = request.POST['otp']
            signup_info = request.session.get('signup_info', {})

            if not signup_info:
                messages.error(request, 'Session expired. Please try signing up again.')
                return redirect('signup')

            otp_generation_time = timezone.datetime.fromisoformat(signup_info.get('otp_generation_time'))
            current_time = timezone.now()
            otp_validity_period = timezone.timedelta(minutes=5)

            if current_time - otp_generation_time > otp_validity_period:
                messages.error(request, 'OTP expired. Please request a new one.')
                return redirect('signup')

            if otp == signup_info.get('otp'):
                user = User.objects.create_user(
                    username=signup_info['username'],
                    email=signup_info['email'],
                    password=signup_info['password']
                )
                user.save()
                messages.success(request, 'Account created successfully!')

                send_mail(
                    'Congratulations on Your Registration',
                    'Congratulations! Your registration is complete.',
                    settings.DEFAULT_FROM_EMAIL,
                    [signup_info['email']],
                    fail_silently=False,
                )

                del request.session['signup_info']
                return redirect('login')
            else:
                messages.error(request, 'Invalid OTP. Please try again.')

        else:  # If OTP is not being submitted, handle user registration
            username = request.POST['username']
            email = request.POST['email']
            password = request.POST['password']

            username_pattern = re.compile(r"^[a-zA-Z0-9._'\-]+$")
            password_pattern = re.compile(
                r'^(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_+{}":;\'])([a-zA-Z\d!@#$%^&*()_+{}":;\']{8,})$')

            if not username_pattern.match(username):
                messages.error(request, 'Username contains invalid characters.')
                return redirect('signup')

            if not password_pattern.match(password):
                messages.error(request,
                               'Password must contain at least one uppercase letter, one special character, one number, and be at least 8 characters long.')
                return redirect('signup')

            if User.objects.filter(username=username).exists():
                messages.error(request, 'Username already exists.')
                return redirect('signup')

            if User.objects.filter(email=email).exists():
                messages.error(request, 'Email already exists.')
                return redirect('signup')

            otp = generate_otp()
            otp_generation_time = timezone.now()

            request.session['signup_info'] = {
                'username': username,
                'email': email,
                'password': password,
                'otp': otp,
                'otp_generation_time': otp_generation_time.isoformat()
            }

            send_mail(
                'Your OTP Code',
                f'Your OTP code is {otp}',
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )

            messages.success(request, 'OTP has been sent to your email. Please enter it below.')

            # Include signup_info in the context to pre-fill the form fields
            context = {
                'username': username,
                'email': email,
                'password': password,
            }
            return render(request, 'signup.html', context)

    # If GET request or other cases, render an empty form
    return render(request, 'signup.html')



@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(username=username, password=password)

        if user is not None:
            auth.login(request, user)
            return redirect('deals_view')
        else:
            messages.error(request, 'Invalid credentials.')

    return render(request, 'login.html')


@login_required
def comment_view(request, deal_id):
    deal = get_object_or_404(Deal, id=deal_id)

    # Retrieve the comments for the deal
    comments = Comment.objects.filter(deal=deal).order_by('-created_at')

    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)  # Create the comment instance but don't save it yet
            comment.user = request.user  # Associate the comment with the current user
            comment.deal = deal  # Associate the comment with the specific deal
            comment.save()  # Save the comment to the database
            messages.success(request, 'Comment submitted successfully!')  # Success message
            return redirect('comment_view', deal_id=deal_id)  # Redirect back to the same view
        else:
            messages.error(request, 'Please correct the errors below.')  # Error message

    else:
        form = CommentForm()  # Instantiate a new form for GET request

    return render(request, 'comment.html', {
        'deal': deal,
        'form': form,
        'comments': comments
    })

@login_required
def deals_view(request):
    # Fetch deals from the database and group by deal_type
    deals = Deal.objects.all()
    deals_by_type = {}

    for deal in deals:
        if deal.deal_type not in deals_by_type:
            deals_by_type[deal.deal_type] = []
        deals_by_type[deal.deal_type].append(deal)

    # Pass the grouped deals to the template
    return render(request, 'deal_list.html', {'deals_by_type': deals_by_type})

@login_required
def update_deal_view(request, deal_id):
    # Check if the user is a superuser or staff member
    if request.user.is_superuser or request.user.is_staff:
        deal = get_object_or_404(Deal, id=deal_id)

        if request.method == 'POST':
            # Update deal attributes based on the submitted form data
            deal.image = request.POST.get('image')
            deal.deal_type = request.POST.get('deal_type')
            deal.price_range = request.POST.get('price_range')
            deal.save()  # Save the updated deal

            return redirect('deals_view')  # Redirect to the deals view after successful update

        # Render a template for updating the deal (GET request)
        return render(request, 'update_deal.html', {'deal': deal})

    # If the user is not authorized, return a forbidden response
    return HttpResponseForbidden("You do not have permission to access this page.")


@never_cache
def logout_view(request):
    logout(request)  # Log the user out

    return redirect(reverse('index'))


@login_required
def deal_detail(request, deal_id):
    deal = get_object_or_404(Deal, id=deal_id)
    return render(request, 'deal_detail.html', {'deal': deal})


JAZZCASH_MERCHANT_ID = "MC118370"
JAZZCASH_PASSWORD = "v5552zt5w3"
JAZZCASH_RETURN_URL = "http://127.0.0.1:8000/success/"
JAZZCASH_INTEGRITY_SALT = "09059375yz"

@login_required
def jazzcash_payment(request):
    product_name = request.session.get('product_name', 'Default Product Name')
    quantity = request.session.get('quantity', 1)
    total = request.session.get('total', 0.0)
    integer_value = int(float(total))
    print(type(integer_value))
    product_price = integer_value

    pp_Amount = product_price

    current_datetime = datetime.now()
    pp_TxnDateTime = current_datetime.strftime('%Y%m%d%H%M%S')

    expiry_datetime = current_datetime + timedelta(hours=1)
    pp_TxnExpiryDateTime = expiry_datetime.strftime('%Y%m%d%H%M%S')

    pp_TxnRefNo = "T" + pp_TxnDateTime
    post_data = {
        "pp_Version": "1.0",
        "pp_TxnType": "",
        "pp_Language": "EN",
        "pp_MerchantID": JAZZCASH_MERCHANT_ID,
        "pp_SubMerchantID": "",
        "pp_Password": JAZZCASH_PASSWORD,
        "pp_BankID": "TBANK",
        "pp_ProductID": "RETL",
        "pp_TxnRefNo": pp_TxnRefNo,
        "pp_Amount": pp_Amount,
        "pp_TxnCurrency": "PKR",
        "pp_TxnDateTime": pp_TxnDateTime,
        "pp_BillReference": "billRef",
        "pp_Description": "Description of transaction",
        "pp_TxnExpiryDateTime": pp_TxnExpiryDateTime,
        "pp_ReturnURL": JAZZCASH_RETURN_URL,
        "pp_SecureHash": "",
        "ppmpf_1": "1",
        "ppmpf_2": "2",
        "ppmpf_3": "3",
        "ppmpf_4": "4",
        "ppmpf_5": "5"
    }

    sorted_string = "&".join(f"{key}={value}" for key, value in sorted(post_data.items()) if value != "")
    pp_SecureHash = hmac.new(
        JAZZCASH_INTEGRITY_SALT.encode(),
        sorted_string.encode(),
        hashlib.sha256
    ).hexdigest()
    post_data['pp_SecureHash'] = pp_SecureHash

    context = {
        'product_name': product_name,
        "product_price": product_price,
        "quantity": quantity,
        'post_data': post_data
    }

    return render(request, 'jazzcash.html', context)

@csrf_exempt
def jazzcash_response(request):
    # Here you can capture the payment response sent by JazzCash
    transaction_id = request.GET.get('pp_TxnRefNo')
    amount = request.GET.get('pp_Amount')
    payment_status = request.GET.get('pp_ResponseCode')

    if payment_status == '000':
        # Payment success
        return HttpResponse("Payment successful")
    else:
        # Payment failed
        return HttpResponse("Payment failed")


@login_required
def checkout_view(request):
    # Extract product details from GET request
    product_name = request.GET.get('name', '')
    quantity = request.GET.get('quantity', '')
    total = request.GET.get('total', '')

    request.session['product_name'] = product_name
    request.session['quantity'] = quantity
    request.session['total'] = total
    order_success = False

    # Initialize the form
    form = AddressForm()

    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            # Save form data
            form.save()

            # Extracting user details from the form
            full_name = form.cleaned_data.get('full_name')
            phone_number = form.cleaned_data.get('phone_number')
            email = form.cleaned_data.get('email')
            address = form.cleaned_data.get('address')

            # Store user information in session
            request.session['full_name'] = full_name
            request.session['phone_number'] = phone_number
            request.session['email'] = email
            request.session['address'] = address

            user = request.user
            # Logic to send WhatsApp message to owner
            owner_number = '+923218802309'  # Replace with the actual owner's phone number
            if user is None:
                message = f"New Order: {product_name}, Quantity: {quantity}, Amount: ₨{total}, Customer: {full_name}, Phone: {phone_number}, Email: {email}, Address: {address}"
            else:
                message = f"New Order: {product_name}, Quantity: {quantity}, Amount: ₨{total}, Customer: {user.username}, Phone: {phone_number}, Email: {user.email}, Address: {address}"

            # Send the WhatsApp message
            account_sid = 'ACe2bfbc5d7b9672f883c2c986ca260661'
            auth_token = 'fd89f95a51d9c182ff83776428b41d40'
            client = Client(account_sid, auth_token)

            client.messages.create(
                body=message,
                from_='whatsapp:+14155238886',  # Twilio sandbox number
                to=f'whatsapp:{owner_number}'
            )

            return redirect('/deals_view/')  # Redirect after successful order placement

    # Pre-fill user information if the user is authenticated
    user = request.user  # Get the authenticated user
    context = {
        'product_name': product_name,
        'quantity': quantity,
        'total': total,
        'order_success': order_success,  # Initially, no order is placed
        'full_name': user.username if user.is_authenticated else '',  # Pre-fill user's full name
        'phone_number': user.profile.phone_number if hasattr(user, 'profile') else '',
        'email': user.email if user.is_authenticated else '',  # Pre-fill user's email
        'address': user.profile.address if hasattr(user, 'profile') else '',
        'form': form
    }

    return render(request, 'checkout.html', context)


def cashjazz(request):
    return render(request, "jazzcash.html")


def success_get(request):
    product_name = request.session.get('product_name', 'Default Product Name')
    quantity = request.session.get('quantity', 1)
    total = request.session.get('total', 0.0)
    full_name = request.session.get('full_name')
    phone_number = request.session.get('phone_number')
    email = request.session.get('email')
    address = request.session.get('address')
    message = f"New Order: {product_name}, Quantity: {quantity}, Amount: ₨{total}, Customer: {full_name}, Phone: {phone_number}, Email: {email}, Address: {address}, Payment: Payment has been done successfully through jazzcash"
    account_sid = 'ACe2bfbc5d7b9672f883c2c986ca260661'
    auth_token = 'fd89f95a51d9c182ff83776428b41d40'
    client = Client(account_sid, auth_token)

    message = client.messages.create(
        body=message,
        from_='whatsapp:+14155238886',  # Twilio sandbox number
        to='whatsapp:+923218802309'  # Your recipient number
    )
    return render(request, 'success.html')
